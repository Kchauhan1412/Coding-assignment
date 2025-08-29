import asyncio
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Iterable
from playwright.async_api import Page, async_playwright

Square = Tuple[int, int]

# While running this suite in chromium please click orange piece and move diagonally

@dataclass
class BoardState:


    pieces: Dict[str, str]

    @classmethod
    async def from_page(cls, page: Page) -> "BoardState":

        pieces: Dict[str, str] = {}
        # Query all image elements on the board.
        images = await page.query_selector_all("#board img")
        for img in images:
            # The ``name`` attribute encodes the coordinate as spaceXY.
            name = await img.get_attribute("name")
            if not name:
                continue

            src = await img.get_attribute("src")
            filename = src.split("/")[-1] if src else ""
            pieces[name] = filename
        return cls(pieces)

    def player_pieces(self) -> Iterable[Square]:

        for name, src in self.pieces.items():
            if src == "you1.gif":
                # name is of the form spaceXY where X and Y are digits.
                x, y = int(name[5]), int(name[6])
                yield (x, y)

    def opponent_pieces(self) -> Iterable[Square]:
        """Return the set of coordinates occupied by opponent pieces."""
        for name, src in self.pieces.items():
            if src == "me1.gif":
                x, y = int(name[5]), int(name[6])
                yield (x, y)

    def empty_playable_squares(self) -> Iterable[Square]:
        """Return the coordinates of empty, playable dark squares."""
        for name, src in self.pieces.items():
            if src == "gray.gif":
                x, y = int(name[5]), int(name[6])
                yield (x, y)


async def wait_for_turn(page: Page) -> None:

    await page.wait_for_selector("#message")
    # Use ``wait_for_function`` to poll until the message includes our prompt. The inline function runs in the browser context.
    await page.wait_for_function(
        "() => document.querySelector('#message').innerText.trim().startsWith('Make a move')"
    )


async def perform_move(page: Page, from_sq: Square, to_sq: Square) -> None:

    fx, fy = from_sq
    tx, ty = to_sq
    # Click the piece to select it.
    await page.click(f"img[name=space{fx}{fy}]")
    # Click the destination square.
    await page.click(f"img[name=space{tx}{ty}]")


def find_capture_move(state: BoardState) -> Optional[Tuple[Square, Square]]:

    # Convert to sets for faster tests.
    opponents = set(state.opponent_pieces())
    empties = set(state.empty_playable_squares())
    for x, y in state.player_pieces():
        for dx in (-2, 2):
            dest_x = x + dx
            dest_y = y + 2
            # Check that the destination is on the board.
            if not (0 <= dest_x <= 7 and 0 <= dest_y <= 7):
                continue
            mid_x = x + dx // 2
            mid_y = y + 1
            if (mid_x, mid_y) in opponents and (dest_x, dest_y) in empties:
                return ( (x, y), (dest_x, dest_y) )
    return None


def find_simple_move(state: BoardState) -> Optional[Tuple[Square, Square]]:
    empties = set(state.empty_playable_squares())
    for x, y in state.player_pieces():
        for dx in (-1, 1):
            dest_x = x + dx
            dest_y = y + 1
            if 0 <= dest_x <= 7 and 0 <= dest_y <= 7:
                if (dest_x, dest_y) in empties:
                    return ( (x, y), (dest_x, dest_y) )
    return None


async def make_moves(page: Page, number_of_moves: int) -> None:
    for _ in range(number_of_moves):
        # Wait until it is our turn.
        await wait_for_turn(page)
        # Take a snapshot of the current board.
        state = await BoardState.from_page(page)
        move = find_capture_move(state)
        if not move:
            move = find_simple_move(state)
        if not move:
            print("No moves available , ending game.")
            return
        (from_sq, to_sq) = move
        await perform_move(page, from_sq, to_sq)

        await page.wait_for_timeout(500)


async def restart_game(page: Page) -> None:
    await page.click("text=Restart...")
    await page.wait_for_function(
        "() => {\n"
        "  const imgs = Array.from(document.querySelectorAll('#board img'));\n"
        "  const you = imgs.filter(i => i.getAttribute('src').endsWith('you1.gif')).length;\n"
        "  const me  = imgs.filter(i => i.getAttribute('src').endsWith('me1.gif')).length;\n"
        "  return you === 12 && me === 12;\n"
        "}"
    )


async def run_checkers_demo() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://www.gamesforthebrain.com/game/checkers/")
        await page.wait_for_selector("#board")
        await make_moves(page, number_of_moves=5)
        await restart_game(page)
        print("Game successfully restarted.")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(run_checkers_demo())