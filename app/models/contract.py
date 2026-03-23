from typing import Optional
from sqlalchemy import String, Text, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    # Client data
    vorname: Mapped[str] = mapped_column(String(100))
    nachname: Mapped[str] = mapped_column(String(100))
    strasse: Mapped[str] = mapped_column(String(200))
    plz_ort: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    mobil: Mapped[str] = mapped_column(String(50))

    # Contract terms
    betrag_gesamt: Mapped[int] = mapped_column(Integer)
    raten: Mapped[int] = mapped_column(Integer, default=0)
    rate: Mapped[int] = mapped_column(Integer, default=0)
    startdatum: Mapped[str] = mapped_column(String(10))
    wochen: Mapped[int] = mapped_column(Integer, default=14)
    bonus: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    # Rendered HTML (immutable snapshot)
    contract_html: Mapped[str] = mapped_column(Text)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[str] = mapped_column(String(30))
    expires_at: Mapped[str] = mapped_column(String(30))

    # Signing data
    signed_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    signed_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    signed_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    signed_user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    @property
    def full_name(self) -> str:
        return f"{self.vorname} {self.nachname}"

    @property
    def is_expired(self) -> bool:
        from datetime import datetime
        if self.status == "signed":
            return False
        try:
            exp = datetime.fromisoformat(self.expires_at)
            return datetime.now() > exp
        except (ValueError, TypeError):
            return False

    @property
    def status_label(self) -> str:
        if self.status == "signed":
            return "Unterschrieben"
        if self.is_expired:
            return "Abgelaufen"
        return "Offen"
