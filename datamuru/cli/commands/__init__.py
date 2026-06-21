from .agile import agile_group
from .apply import apply_command
from .destroy import destroy_command
from .doctor import doctor_command
from .edition import edition_group
from .enterprise import enterprise_group
from .init import init_command
from .import_ import import_group
from .plan import plan_command
from .state import state_group
from .validate import validate_command

COMMANDS = [
    init_command,
    validate_command,
    plan_command,
    apply_command,
    destroy_command,
    doctor_command,
    import_group,
    state_group,
    edition_group,
    enterprise_group,
    agile_group,
]
