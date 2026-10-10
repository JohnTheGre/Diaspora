from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Country(Base):
    __tablename__ = "countries"
    id = Column(Integer, primary_key=True)
    iso_code = Column(String(3), unique=True, index=True)
    name = Column(String, unique=True)
    avg_height_cm = Column(Float, nullable=True)
    avg_weight_kg = Column(Float, nullable=True)

    languages = relationship("LanguageSpeakers", back_populates="country")
    diaspora_populations = relationship("DiasporaPopulation", back_populates="country")


class LanguageSpeakers(Base):
    __tablename__ = "language_speakers"
    id = Column(Integer, primary_key=True)
    country_id = Column(Integer, ForeignKey("countries.id"))
    language = Column(String, index=True)
    rank = Column(Integer)            # 1 = L1, 2 = L2, ...
    percentage = Column(Float)        # e.g. 59.3

    country = relationship("Country", back_populates="languages")



class DiasporaPopulation(Base):
    __tablename__ = "diaspora_population"

    id = Column(Integer, primary_key=True)

    # The destination country being highlighted on the globe
    country_id = Column(
        Integer,
        ForeignKey("countries.id"),
        nullable=False,
        index=True
    )

    # The country selected by the user
    origin_country = Column(String, nullable=False, index=True)
    origin_iso3 = Column(String(3), nullable=False, index=True)

    # The destination country
    destination_country = Column(String, nullable=False)
    destination_iso3 = Column(String(3), nullable=False, index=True)

    # Nullable because most seed rows do not have verified counts
    population_count = Column(Integer, nullable=True)
    estimate_year = Column(Integer, nullable=True)

    record_status = Column(String, nullable=False)
    confidence = Column(String, nullable=True)
    source_url = Column(String, nullable=True)

    country = relationship(
        "Country",
        back_populates="diaspora_populations"
    )