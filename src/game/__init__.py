"""Game automation package"""

from .navigation import (
    navigate_home,
    launch_game,
    open_secretary_menu,
    open_profile_menu,
)

from .secretary_automation import (
    process_secretary_position,
    run_secretary_loop,
    exit_to_secretary_menu,
    verify_secretary_menu
)

from .controls import (
    human_delay,
    humanized_tap,
    handle_swipes
) 

from .alliance_donate import (
    run_alliance_donate
)