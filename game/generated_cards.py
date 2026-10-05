"""Combat-local card creation policy; reward and permanent-deck factories stay unchanged."""
from contextvars import ContextVar

combat_creation_state = ContextVar('combat_creation_state', default=None)


def prepare_created_card(card, state=None):
    state = state or combat_creation_state.get()
    if state is None or not state.player.statuses.get('w_master_reality'):
        return card
    from data.card.upgrade_rules import has_upgrade, upgrade_card
    return upgrade_card(card) if has_upgrade(card) else card
