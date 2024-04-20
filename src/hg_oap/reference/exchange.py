from datetime import date

from hgraph import CompoundScalar

from hg_oap.reference.country_data import Country


class Exchange(CompoundScalar):
    mic: str  # Market Identifier Code
    op_mic: str  # Operating Market Identifier Code
    name: str
    legal_entity_name: str
    acronym: str
    country: Country
    city: str
    creation_date: date
    expiration_date: date | None = None

