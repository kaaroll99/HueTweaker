"""Offline checks of the pure logic. Run from the repository root: ``python3 -m tests.test_logic`` (or pytest)."""

import asyncio
import functools

from utils.color_format import decode_slots, decode_style
from utils.history_manager import pack_color, unpack_color
from utils.role_manager import move_roles_to_block


@functools.total_ordering
class FakeRole:
    def __init__(self, role_id: int, name: str):
        self.id, self.position, self.name = role_id, role_id, name

    def is_default(self) -> bool:
        return self.position == 0

    def __lt__(self, other):
        return (self.position, self.id) < (other.position, other.id)

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return self.id


class FakeGuild:
    async def edit_role_positions(self, payload, reason=None):
        for role, position in payload.items():
            role.position = position


def place(names: str, block: str, top_position) -> str:
    """Place the ``block`` roles below ``top_position`` (a role name, or a number) and return the new order."""
    roles = [FakeRole(i, name) for i, name in enumerate(["@everyone", *names.split()])]
    if isinstance(top_position, str):
        top_position = next(r.position for r in roles if r.name == top_position) - 1
    ids = {r.id for r in roles if r.name in block.split()}
    asyncio.run(move_roles_to_block(FakeGuild(), ids, top_position, roles=roles))
    return " ".join(r.name for r in sorted(roles) if not r.is_default())


def test_block_below_reference_stays():
    assert place("a b c1 c2 REF bot", "c1 c2", "REF") == "a b c1 c2 REF bot"


def test_block_above_reference_moves_right_below_it():
    # Switching from auto (block under the bot) to a lower custom role.
    assert place("a b c d REF c1 c2 bot", "c1 c2", "REF") == "a b c d c1 c2 REF bot"


def test_off_puts_block_at_bottom():
    assert place("a c1 b c2 bot", "c1 c2", 0) == "c1 c2 a b bot"


def test_auto_puts_block_under_bot():
    assert place("c1 a c2 b bot top", "c1 c2", "bot") == "a b c1 c2 bot top"


def test_history_pack_round_trip():
    for colors in [(0xFF0000, None, None), (0x123456, 0xABCDEF, None), (0xA9C9FF, 0xFFBBEC, 0xFFC3A0)]:
        assert unpack_color(pack_color(*colors)) == colors


def test_decode_skips_bad_values():
    assert decode_style("#ff0000") == (0xFF0000, None, None)
    assert decode_style("ff0000+00ff00") == (0xFF0000, 0x00FF00, None)
    for bad in [None, "", "zzzzzz", "ff0000+", "a+b+c+d", "ff00"]:
        assert decode_style(bad) is None
    assert decode_slots({"hex_1": "bad", "hex_3": "00ff00"}) == [(3, (0x00FF00, None, None))]
    assert decode_slots(None) == []


if __name__ == "__main__":
    tests = [f for name, f in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"{len(tests)} tests passed")
