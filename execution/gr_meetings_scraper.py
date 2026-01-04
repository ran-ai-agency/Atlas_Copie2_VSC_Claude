#!/usr/bin/env python3
"""
GR International - Extracteur des Réunions du Groupe Vaudreuil-Dorion 1
Extrait les détails de toutes les réunions (dates, liens enregistrés, participants)
et génère un fichier JSON structuré pour l'analyse.
"""

import os
import re
import json
import sys
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Configuration
BASE_URL = "https://www.grinternational.ca"
MEETINGS_URL = "https://www.grinternational.ca/membres/reunions/?reunion=Vk14TmREYWFXM0dyVnhvV2RyOVFDMzQ3bEk4PTo6NWZiNjBhMzQ5NzQ3YTk4YWVjZTI0Y2Q4MzU4YWMwMjg"
MEMBER_TOKEN_URL = os.getenv('GR_MEMBER_URL', '')


@dataclass
class MeetingLink:
    """Représente un lien enregistré lors d'une réunion"""
    member_name: str
    company: str
    link_type: str  # "Donne", "Recu", "Referral", etc.
    target_name: Optional[str] = None
    target_company: Optional[str] = None
    notes: Optional[str] = None
    amount: Optional[float] = None  # Montant si applicable


@dataclass
class Visitor:
    """Représente un visiteur/invité à une réunion"""
    name: str
    company: str = ""
    email: str = ""
    phone: str = ""
    referred_by: str = ""
    is_member: bool = False


@dataclass
class Meeting:
    """Représente une réunion du groupe"""
    date: str  # Format YYYY-MM-DD
    group: str
    present_count: int = 0
    absent_count: int = 0
    visitors_count: int = 0
    links_given: int = 0
    links_received: int = 0
    referrals_count: int = 0
    closed_business: float = 0.0  # Montant des affaires conclues
    transactions_count: int = 0
    members_present: List[str] = field(default_factory=list)
    members_absent: List[str] = field(default_factory=list)
    visitors: List[Dict[str, Any]] = field(default_factory=list)  # Liste détaillée des visiteurs
    links: List[Dict[str, Any]] = field(default_factory=list)
    # Section Trucs
    toolbox_presenter: str = ""  # Qui a fait la boîte à outils
    toolbox_subject: str = ""    # Sujet de la boîte à outils
    # Section Autres
    total_attendees: int = 0     # Number of attendee
    form_completed_by: str = ""  # Qui a rempli le formulaire
    notes: str = ""
    detail_url: Optional[str] = None

    def to_dict(self):
        return asdict(self)


class GRMeetingsScraper:
    """Scraper pour extraire les réunions du groupe Vaudreuil-Dorion 1"""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.page = None
        self.authenticated = False
        self.meetings: List[Meeting] = []

    def start_browser(self):
        """Démarre le navigateur Playwright"""
        from playwright.sync_api import sync_playwright

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        self.page = self.context.new_page()
        print("[OK] Navigateur demarré")

    def close_browser(self):
        """Ferme le navigateur"""
        if self.browser:
            self.browser.close()
        if hasattr(self, 'playwright'):
            self.playwright.stop()
        print("[OK] Navigateur fermé")

    def authenticate(self) -> bool:
        """Authentification via le lien membre avec token"""
        member_url = MEMBER_TOKEN_URL

        if not member_url:
            print("[ERROR] GR_MEMBER_URL non configuré dans .env")
            return False

        try:
            print("[AUTH] Connexion via lien membre...")
            self.page.goto(member_url, wait_until='networkidle', timeout=30000)
            self.page.wait_for_timeout(3000)

            # Vérifier si on est connecté
            content = self.page.content().lower()
            if 'member' in content or 'membre' in content or 'welcome' in content or 'bienvenue' in content:
                self.authenticated = True
                print("[OK] Authentification réussie")

                # Sauvegarder capture
                tmp_dir = Path(__file__).parent.parent / ".tmp"
                tmp_dir.mkdir(exist_ok=True)
                self.page.screenshot(path=str(tmp_dir / "gr_meetings_auth.png"))
                return True
            else:
                print("[WARN] Page chargée mais authentification non confirmée")
                return True  # Continuer quand même

        except Exception as e:
            print(f"[ERROR] Erreur d'authentification: {e}")
            return False

    def fetch_meetings_list(self) -> List[Dict[str, Any]]:
        """Récupère la liste des réunions avec leurs IDs de formulaire"""
        meetings_info = []
        tmp_dir = Path(__file__).parent.parent / ".tmp"
        tmp_dir.mkdir(exist_ok=True)

        try:
            print("[MEETINGS] Navigation vers la page des réunions...")
            self.page.goto(MEETINGS_URL, wait_until='networkidle', timeout=30000)
            self.page.wait_for_timeout(3000)
            self.page.screenshot(path=str(tmp_dir / "gr_meetings_list.png"))

            # Sauvegarder le HTML pour analyse
            html_content = self.page.content()
            (tmp_dir / "gr_meetings_list.html").write_text(html_content, encoding='utf-8')

            # La structure est: chaque réunion a un formulaire avec:
            # - input[name="ReunionID"] contenant l'ID
            # - input[type="submit"][value="Consulter"] comme bouton
            # Les formulaires sont dans des lignes de tableau avec la date

            rows = self.page.locator('table tbody tr').all()
            print(f"   -> {len(rows)} lignes trouvées dans le tableau")

            for row in rows:
                try:
                    row_text = row.inner_text().strip()

                    # Chercher une date au format YYYY-MM-DD
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', row_text)
                    if date_match:
                        meeting_date = date_match.group(1)

                        # Chercher l'input ReunionID dans le formulaire
                        reunion_id_input = row.locator('input[name="ReunionID"]').first
                        reunion_id = None
                        if reunion_id_input.count() > 0:
                            reunion_id = reunion_id_input.get_attribute('value')

                        # Chercher le formulaire pour l'action URL
                        form = row.locator('form').first
                        form_action = None
                        if form.count() > 0:
                            form_action = form.get_attribute('action')

                        meetings_info.append({
                            'date': meeting_date,
                            'reunion_id': reunion_id,
                            'form_action': form_action
                        })

                except Exception as e:
                    continue

            # Dédupliquer par date
            seen_dates = set()
            unique_meetings = []
            for m in meetings_info:
                if m['date'] not in seen_dates:
                    seen_dates.add(m['date'])
                    unique_meetings.append(m)

            print(f"   -> {len(unique_meetings)} réunions uniques identifiées")
            return unique_meetings

        except Exception as e:
            print(f"[ERROR] Erreur récupération liste: {e}")
            return []

    def extract_meeting_details(self, date: str, reunion_id: Optional[str], form_action: Optional[str]) -> Meeting:
        """Extrait les détails complets d'une réunion en soumettant le formulaire"""
        meeting = Meeting(
            date=date,
            group="Vaudreuil-Dorion 1",
            detail_url=form_action
        )

        if not reunion_id:
            print(f"   -> [{date}] Pas d'ID de réunion")
            return meeting

        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"   -> [{date}] Soumission du formulaire (ID: {reunion_id})...")

                # Toujours retourner à la page des réunions pour chaque extraction
                # Ajouter un délai avant pour éviter le rate limiting
                self.page.wait_for_timeout(1500)
                self.page.goto(MEETINGS_URL, wait_until='domcontentloaded', timeout=60000)
                self.page.wait_for_timeout(3000)

                # Trouver et cliquer sur le bouton Consulter pour cette réunion
                # Le formulaire a l'ID fXXXXX où XXXXX est le ReunionID
                form_selector = f'form#f{reunion_id}'
                submit_btn = self.page.locator(f'{form_selector} input[type="submit"]').first

                if submit_btn.count() > 0:
                    submit_btn.click()
                    self.page.wait_for_load_state('domcontentloaded', timeout=30000)
                    self.page.wait_for_timeout(2000)
                    break  # Succès, sortir de la boucle de retry
                else:
                    print(f"      [WARN] Bouton Consulter non trouvé pour ID {reunion_id}")
                    return meeting

            except Exception as nav_error:
                if attempt < max_retries - 1:
                    print(f"      [RETRY] Tentative {attempt + 2}/{max_retries} après erreur...")
                    self.page.wait_for_timeout(5000)  # Attendre 5 secondes avant de réessayer
                else:
                    print(f"      [ERREUR] {str(nav_error)[:50]}")
                    return meeting

        # Sauvegarder capture et HTML pour analyse
        tmp_dir = Path(__file__).parent.parent / ".tmp"
        try:
            self.page.screenshot(path=str(tmp_dir / f"gr_meeting_{date}.png"))
            html_content = self.page.content()
            (tmp_dir / f"gr_meeting_{date}.html").write_text(html_content, encoding='utf-8')

            # Extraire les données du tableau "Présence des membres"
            # Structure: Membre | Présence | Références | Transactions complétées
            try:
                member_table = self.page.locator('table.table-reunion tbody').first
                if member_table.count() > 0:
                    rows = member_table.locator('tr').all()
                    total_references = 0
                    total_transactions = 0

                    for row in rows:
                        cells = row.locator('td').all()
                        if len(cells) >= 4:
                            # Colonne 0: Nom du membre avec rôle (ex: "Cormier, Nathalie  (P)")
                            member_name = cells[0].inner_text().strip()

                            # Colonne 1: Présence (Présent/Absent)
                            presence = cells[1].inner_text().strip()

                            # Colonne 2: Références (nombre)
                            references = 0
                            try:
                                references = int(cells[2].inner_text().strip())
                            except:
                                pass

                            # Colonne 3: Transactions complétées (nombre)
                            transactions = 0
                            try:
                                transactions = int(cells[3].inner_text().strip())
                            except:
                                pass

                            # Ajouter aux listes et totaux
                            if 'Présent' in presence or 'Present' in presence:
                                meeting.present_count += 1
                                meeting.members_present.append(member_name)
                            elif 'Absent' in presence:
                                meeting.absent_count += 1
                                meeting.members_absent.append(member_name)

                            total_references += references
                            total_transactions += transactions

                            # Ajouter un enregistrement de lien pour ce membre
                            if references > 0 or transactions > 0:
                                meeting.links.append({
                                    'member': member_name,
                                    'references': references,
                                    'transactions': transactions
                                })

                    meeting.referrals_count = total_references
                    meeting.closed_business = float(total_transactions)  # Utilisé comme compteur de transactions

            except Exception as e:
                print(f"      [WARN] Erreur extraction tableau: {str(e)[:50]}")

            # Extraire la liste des invités (visiteurs)
            try:
                visitors_table = self.page.locator('h3:has-text("invités") + table, h3.view:has-text("invités") ~ table').first
                if visitors_table.count() == 0:
                    # Essayer le deuxième tableau de la page
                    visitors_table = self.page.locator('table.table-reunion').nth(1)

                if visitors_table.count() > 0:
                    visitor_rows = visitors_table.locator('tbody tr').all()
                    for vrow in visitor_rows:
                        try:
                            cells = vrow.locator('td').all()
                            if len(cells) >= 1:
                                cell_html = cells[0].inner_html()
                                cell_text = cells[0].inner_text().strip()

                                # Parser les informations du visiteur
                                visitor_data = {
                                    'name': '',
                                    'company': '',
                                    'email': '',
                                    'phone': '',
                                    'referred_by': '',
                                    'is_member': False
                                }

                                # Extraire le nom et l'entreprise (première ligne)
                                lines = [l.strip() for l in cell_text.split('\n') if l.strip()]
                                if lines:
                                    first_line = lines[0]
                                    if ',' in first_line:
                                        parts = first_line.split(',')
                                        visitor_data['name'] = parts[0].strip() + ', ' + parts[1].strip() if len(parts) > 1 else parts[0].strip()
                                        visitor_data['company'] = ', '.join(parts[2:]).strip() if len(parts) > 2 else ''

                                # Extraire l'email
                                email_match = re.search(r'mailto:([^"]+)"', cell_html)
                                if email_match:
                                    visitor_data['email'] = email_match.group(1)

                                # Extraire le téléphone
                                phone_match = re.search(r'[\d-]{10,}', cell_text)
                                if phone_match:
                                    visitor_data['phone'] = phone_match.group(0)

                                # Extraire "Référé par"
                                refere_match = re.search(r'Référé par\s+(.+?)(?:\s*$|\s*\n)', cell_text)
                                if refere_match:
                                    visitor_data['referred_by'] = refere_match.group(1).strip()

                                # Vérifier si c'est un membre (colonne 2)
                                if len(cells) >= 2:
                                    member_text = cells[1].inner_text().strip().lower()
                                    visitor_data['is_member'] = 'oui' in member_text or 'yes' in member_text

                                if visitor_data['name']:
                                    meeting.visitors.append(visitor_data)
                                    meeting.visitors_count += 1
                        except:
                            continue
            except Exception as e:
                pass

            # Extraire la section "Trucs" (Boîte à outils GR)
            try:
                trucs_section = self.page.locator('h3:has-text("Trucs")').first
                if trucs_section.count() > 0:
                    # Chercher le conteneur parent
                    parent = trucs_section.locator('xpath=..').first
                    parent_text = parent.inner_text() if parent.count() > 0 else ''

                    # Qui a fait la boîte à outils
                    presenter_match = re.search(r'Qui a fait la boîte à outils GR\?\s*[–-]\s*(.+?)(?:\n|$)', parent_text)
                    if presenter_match:
                        meeting.toolbox_presenter = presenter_match.group(1).strip()

                    # Sujet de la boîte à outils
                    subject_match = re.search(r'Sujet de la boîte à outils GR\s*[–-]\s*(.+?)(?:\n|$)', parent_text)
                    if subject_match:
                        meeting.toolbox_subject = subject_match.group(1).strip()
            except:
                pass

            # Extraire la section "Références"
            try:
                ref_section = self.page.locator('h3:has-text("Références")').first
                if ref_section.count() > 0:
                    parent = ref_section.locator('xpath=..').first
                    if parent.count() > 0:
                        parent_text = parent.inner_text()

                        # Nombre de transactions complétées
                        trans_match = re.search(r'transactions complétées\s*:\s*(\d+)', parent_text, re.IGNORECASE)
                        if trans_match:
                            meeting.transactions_count = int(trans_match.group(1))
            except:
                pass

            # Extraire la section "Autres"
            try:
                autres_section = self.page.locator('h3:has-text("Autres")').first
                if autres_section.count() > 0:
                    parent = autres_section.locator('xpath=..').first
                    if parent.count() > 0:
                        parent_text = parent.inner_text()

                        # Number of attendee
                        attendee_match = re.search(r'Number of attendee\s*:\s*(\d+)', parent_text, re.IGNORECASE)
                        if attendee_match:
                            meeting.total_attendees = int(attendee_match.group(1))

                        # Form completed by
                        completed_match = re.search(r'Form completed by\s*:\s*(.+?)(?:\n|$)', parent_text, re.IGNORECASE)
                        if completed_match:
                            meeting.form_completed_by = completed_match.group(1).strip()
            except:
                pass

            # Extraire les notes et commentaires
            try:
                notes_section = self.page.locator('h3:has-text("Notes et commentaires")').first
                if notes_section.count() > 0:
                    # Chercher le paragraphe suivant
                    notes_p = notes_section.locator('xpath=following-sibling::p').first
                    if notes_p.count() > 0:
                        meeting.notes = notes_p.inner_text().strip()
            except:
                pass

            print(f"      [OK] {meeting.present_count} présents, {meeting.absent_count} absents, {meeting.referrals_count} références, {meeting.visitors_count} visiteurs")

        except Exception as e:
            print(f"      [ERREUR] {str(e)[:50]}")

        return meeting

    def run(self, headless: bool = True, max_meetings: int = 0) -> List[Meeting]:
        """Exécute l'extraction complète des réunions"""
        self.headless = headless

        print("=" * 60)
        print("[SCAN] Extraction des réunions GR International")
        print("       Groupe: Vaudreuil-Dorion 1")
        print("=" * 60)

        try:
            self.start_browser()

            if not self.authenticate():
                print("[WARN] Continuant sans authentification confirmée...")

            # Récupérer la liste des réunions
            meetings_list = self.fetch_meetings_list()

            if max_meetings > 0:
                meetings_list = meetings_list[:max_meetings]
                print(f"[INFO] Limité à {max_meetings} réunions")

            print(f"\n[EXTRACT] Extraction des détails de {len(meetings_list)} réunions...")

            for i, meeting_info in enumerate(meetings_list):
                print(f"\n[{i+1}/{len(meetings_list)}] Réunion du {meeting_info['date']}")
                meeting = self.extract_meeting_details(
                    date=meeting_info['date'],
                    reunion_id=meeting_info.get('reunion_id'),
                    form_action=meeting_info.get('form_action')
                )
                self.meetings.append(meeting)

            # Sauvegarder les résultats
            self.save_results()

            return self.meetings

        finally:
            self.close_browser()

    def save_results(self):
        """Sauvegarde les résultats en JSON"""
        tmp_dir = Path(__file__).parent.parent / ".tmp"
        tmp_dir.mkdir(exist_ok=True)

        # Fichier JSON principal
        json_path = tmp_dir / "gr_vaudreuil_meetings.json"

        output_data = {
            "groupe": "Vaudreuil-Dorion 1",
            "derniere_mise_a_jour": datetime.now().isoformat(),
            "total_reunions": len(self.meetings),
            "reunions": [m.to_dict() for m in self.meetings]
        }

        json_path.write_text(
            json.dumps(output_data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        print(f"\n[SAVED] Données JSON: {json_path}")

        # Résumé statistique
        total_links = sum(m.links_given + m.links_received for m in self.meetings)
        total_referrals = sum(m.referrals_count for m in self.meetings)
        total_business = sum(m.closed_business for m in self.meetings)

        summary = f"""# Résumé des Réunions - Vaudreuil-Dorion 1

**Dernière mise à jour**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Total réunions analysées**: {len(self.meetings)}

## Statistiques Globales

- **Total liens échangés**: {total_links}
- **Total référencements**: {total_referrals}
- **Affaires conclues**: ${total_business:,.2f}

## Liste des Réunions

| Date | Présents | Visiteurs | Liens | Affaires |
|------|----------|-----------|-------|----------|
"""
        for m in sorted(self.meetings, key=lambda x: x.date, reverse=True)[:20]:
            summary += f"| {m.date} | {m.present_count} | {m.visitors_count} | {m.links_given + m.links_received} | ${m.closed_business:,.0f} |\n"

        summary_path = tmp_dir / "gr_vaudreuil_summary.md"
        summary_path.write_text(summary, encoding='utf-8')
        print(f"[SAVED] Résumé: {summary_path}")

    def add_new_meeting(self, date: str):
        """Ajoute une nouvelle réunion à la liste existante"""
        # Charger la liste existante
        tmp_dir = Path(__file__).parent.parent / ".tmp"
        json_path = tmp_dir / "gr_vaudreuil_meetings.json"

        existing_data = {"reunions": []}
        if json_path.exists():
            existing_data = json.loads(json_path.read_text(encoding='utf-8'))

        # Vérifier si la date existe déjà
        existing_dates = [m['date'] for m in existing_data.get('reunions', [])]
        if date in existing_dates:
            print(f"[INFO] La réunion du {date} existe déjà")
            return

        # Ajouter la nouvelle réunion
        print(f"[ADD] Ajout de la réunion du {date}")
        self.start_browser()

        try:
            self.authenticate()

            # Naviguer vers la page et trouver le lien pour cette date
            self.page.goto(MEETINGS_URL, wait_until='networkidle', timeout=30000)
            self.page.wait_for_timeout(2000)

            # Chercher la ligne avec cette date
            rows = self.page.locator('table tr').all()
            detail_url = None

            for row in rows:
                row_text = row.inner_text()
                if date in row_text:
                    view_link = row.locator('a:has-text("View"), a:has-text("Consulter")').first
                    if view_link.count() > 0:
                        href = view_link.get_attribute('href')
                        if href:
                            detail_url = href if href.startswith('http') else BASE_URL + href
                    break

            # Extraire les détails
            meeting = self.extract_meeting_details(date, detail_url)

            # Ajouter à la liste
            existing_data['reunions'].insert(0, meeting.to_dict())
            existing_data['derniere_mise_a_jour'] = datetime.now().isoformat()
            existing_data['total_reunions'] = len(existing_data['reunions'])

            # Sauvegarder
            json_path.write_text(
                json.dumps(existing_data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            print(f"[OK] Réunion du {date} ajoutée")

        finally:
            self.close_browser()


def main():
    """Point d'entrée principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Extracteur des réunions GR International')
    parser.add_argument('--visible', action='store_true', help='Mode visible (non headless)')
    parser.add_argument('--max', type=int, default=0, help='Nombre max de réunions à extraire (0 = toutes)')
    parser.add_argument('--add', type=str, help='Ajouter une nouvelle réunion (format: YYYY-MM-DD)')

    args = parser.parse_args()

    scraper = GRMeetingsScraper()

    if args.add:
        # Mode ajout d'une nouvelle réunion
        scraper.add_new_meeting(args.add)
    else:
        # Mode extraction complète
        meetings = scraper.run(headless=not args.visible, max_meetings=args.max)

        print("\n" + "=" * 60)
        print(f"EXTRACTION TERMINÉE: {len(meetings)} réunions")
        print("=" * 60)

        # Afficher un aperçu
        for m in meetings[:5]:
            print(f"  - {m.date}: {m.present_count} présents, {m.links_given} liens donnés")
        if len(meetings) > 5:
            print(f"  ... et {len(meetings) - 5} autres réunions")


if __name__ == "__main__":
    main()
