from enum import StrEnum


class Recurrence(StrEnum):
    """
    Enumeration representing the recurrence frequency of an automation task.

    Each member corresponds to a specific recurrence type and can be stored
    in the database within the 'recorrencia' column. Using this enum
    makes it easier to identify and manage the recurrence of automated processes.

    Members:
        DIARIA (daily)         : Represents daily recurrence.
        SEMANAL (weekly)       : Represents weekly recurrence.
        MENSAL (monthly)       : Represents monthly recurrence.
        ANUAL (annual)         : Represents yearly recurrence.
        SOB_DEMANDA (on demand): No fixed schedule; triggered manually or by an event.

    Usage:
        >>> Recurrence.DIARIA
        <Recurrence.DIARIA: 'diaria'>
        >>> str(Recurrence.DIARIA)
        'diaria'
    """

    DIARIA = "diaria"
    SEMANAL = "semanal"
    MENSAL = "mensal"
    ANUAL = "anual"
    SOB_DEMANDA = "sob demanda"
