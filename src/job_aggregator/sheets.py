from __future__ import annotations

from collections.abc import Iterable

from .models import JobListing, SHEET_HEADERS
from .utils import to_sheet_row


class GoogleSheetsWriter:
    def __init__(self, spreadsheet_id: str, worksheet_name: str, credentials_path: str):
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        self.spreadsheet_id = spreadsheet_id
        self.worksheet_name = worksheet_name
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(credentials_path, scopes=scopes)
        self.service = build("sheets", "v4", credentials=creds)

    def ensure_headers(self) -> None:
        rng = f"{self.worksheet_name}!A1:P1"
        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=rng,
            valueInputOption="RAW",
            body={"values": [SHEET_HEADERS]},
        ).execute()

    def load_existing_index(self) -> dict[str, int]:
        rng = f"{self.worksheet_name}!A2:P"
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=rng,
        ).execute()
        rows = result.get("values", [])
        index = {}
        for row_num, row in enumerate(rows, start=2):
            if len(row) >= 15 and row[14]:
                index[row[14]] = row_num
        return index

    def upsert_jobs(self, jobs: Iterable[JobListing]) -> tuple[int, int]:
        existing = self.load_existing_index()
        updated = 0
        inserted = 0
        append_rows = []
        for job in jobs:
            row = to_sheet_row(job)
            target_row = existing.get(job.canonical_key)
            if target_row:
                rng = f"{self.worksheet_name}!A{target_row}:P{target_row}"
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=rng,
                    valueInputOption="RAW",
                    body={"values": [row]},
                ).execute()
                updated += 1
            else:
                append_rows.append(row)
                inserted += 1

        if append_rows:
            self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{self.worksheet_name}!A:P",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": append_rows},
            ).execute()
        return inserted, updated
