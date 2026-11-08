import csv

from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ner.models import PluviometricStation


EXPECTED_STATIONS = 82


class Command(BaseCommand):

    help = (
        "Importa as estações pluviométricas da "
        "DNIT 182/2018-PRO."
    )

    REQUIRED_FIELDS = {
        "code",
        "name",
        "municipality",
        "state",
        "latitude",
        "longitude",
        "operator",
        "nd",
        "nere",
    }

    def add_arguments(self, parser):

        parser.add_argument(
            "csv_file",
            type=str,
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Valida os dados sem persistir alterações.",
        )

    def handle(self, *args, **options):

        csv_file = options["csv_file"]
        dry_run = options["dry_run"]

        records = self.read_csv(csv_file)

        if len(records) != EXPECTED_STATIONS:
            raise CommandError(
                f"A norma deve conter {EXPECTED_STATIONS} "
                f"estações. Foram encontradas {len(records)}."
            )

        self.validate_unique_codes(records)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "Modo de simulação: nenhuma alteração realizada."
                )
            )

            return

        created = 0
        updated = 0

        with transaction.atomic():

            for record in records:

                _, was_created = (
                    PluviometricStation.objects.update_or_create(
                        code=record["code"],
                        defaults={
                            "name": record["name"],
                            "municipality": record["municipality"],
                            "state": record["state"],
                            "operator": record["operator"],
                            "latitude": record["latitude"],
                            "longitude": record["longitude"],
                            "nd": record["nd"],
                            "nere": record["nere"],
                            "norm_reference": "DNIT 182/2018 - PRO",
                        },
                    )
                )

                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Importação concluída.\n"
                f"Estações cadastradas: {created}\n"
                f"Estações atualizadas: {updated}\n"
                f"Total processado: {created + updated}"
            )
        )

    def read_csv(self, csv_file):

        try:
            with open(
                csv_file,
                mode="r",
                encoding="utf-8-sig",
                newline="",
            ) as file:

                reader = csv.DictReader(file)

                if not reader.fieldnames:
                    raise CommandError(
                        "O CSV não possui cabeçalho."
                    )

                missing = (
                    self.REQUIRED_FIELDS
                    - set(reader.fieldnames)
                )

                if missing:
                    raise CommandError(
                        f"Colunas ausentes: {', '.join(sorted(missing))}"
                    )

                return [
                    self.normalize_record(row, index)
                    for index, row in enumerate(reader, start=2)
                ]

        except OSError as exc:
            raise CommandError(
                f"Erro ao abrir arquivo: {exc}"
            )

    def normalize_record(self, row, line):

        try:

            record = {
                "code": row["code"].strip(),
                "name": row["name"].strip(),
                "municipality": row["municipality"].strip(),
                "state": row["state"].strip().upper(),
                "operator": row["operator"].strip(),
                "latitude": self.to_decimal(row["latitude"]),
                "longitude": self.to_decimal(row["longitude"]),
                "nd": self.to_decimal(row["nd"]),
                "nere": self.to_decimal(row["nere"]),
            }

            if not record["code"]:
                raise ValueError("Código vazio.")

            if not record["name"]:
                raise ValueError("Nome vazio.")

            if len(record["state"]) != 2:
                raise ValueError("UF inválida.")

            if not Decimal("1") <= record["nere"] <= Decimal("12"):
                raise ValueError("NERE fora do intervalo normativo.")

            if not Decimal("-90") <= record["latitude"] <= Decimal("90"):
                raise ValueError("Latitude inválida.")

            if not Decimal("-180") <= record["longitude"] <= Decimal("180"):
                raise ValueError("Longitude inválida.")

            return record

        except (ValueError, InvalidOperation, KeyError) as exc:

            raise CommandError(
                f"Erro na linha {line} do CSV: {exc}"
            )

    @staticmethod
    def to_decimal(value):

        value = value.strip().replace(",", ".")

        if not value:
            return None

        return Decimal(value)

    def validate_unique_codes(self, records):

        codes = [
            record["code"]
            for record in records
        ]

        if len(codes) != len(set(codes)):
            raise CommandError(
                "O arquivo contém códigos de estações duplicados."
            )