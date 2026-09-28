from src.repositories.reserva_repository import ReservaRepository

class Reserva(ReservaRepository):
    """Representa uma reserva no sistema.
    
    Attributes:
        id : Identificação única da reserva.
        dataReserva : Data da reserva.
        dataExpiracao : Data de expiração da reserva.
        adotante : O adotante relacionado.
        animal : O animal relacionado.
        compatibilidade : A pontuação de compatibilidade
        status : Status da reserva.
    """