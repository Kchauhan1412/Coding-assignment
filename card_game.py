from typing import List, Dict
import requests


def check_service_up(url: str) -> None:
    #Perform a GET request to confirm the API response and if not then raise runtime error.
    
    try:
        resp = requests.get(url, timeout=10)
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to reach {url}: {exc}") from exc
    if resp.status_code != 200:
        raise RuntimeError(f"Service at {url} returned HTTP {resp.status_code}")


def get_new_deck() -> str:
    #Request a new deck and return its identifier.
    resp = requests.get("https://deckofcardsapi.com/api/deck/new/")
    resp.raise_for_status()
    data: Dict[str, object] = resp.json()
    return str(data["deck_id"])


def shuffle_deck(deck_id: str) -> None:
    #Shuffle the specified deck in place.
    resp = requests.get(f"https://deckofcardsapi.com/api/deck/{deck_id}/shuffle/")
    resp.raise_for_status()


def deal_cards(deck_id: str, count: int) -> List[Dict[str, object]]:
    #Draw cards from the deck and return their data structures.
    resp = requests.get(
        f"https://deckofcardsapi.com/api/deck/{deck_id}/draw/?count={count}"
    )
    resp.raise_for_status()
    data = resp.json()
    cards: List[Dict[str, object]] = data.get("cards", [])
    if len(cards) != count:
        raise RuntimeError(
            f"Expected {count} cards but received {len(cards)} from the API"
        )
    return cards


def card_point_value(value: str) -> int:
    #Return the blackjack point value of a card given its face value.
    if value in {"JACK", "QUEEN", "KING"}:
        return 10
    if value == "ACE":
    # start by treating aces as 11; may downgrade later
        return 11               
    return int(value)


def hand_total(cards: List[Dict[str, object]]) -> int:
    #Compute the best blackjack total for a hand.
    points = [card_point_value(card["value"]) for card in cards]
    total = sum(points)

    # Count how many aces we have (valued at 11 for now)
    ace_count = sum(1 for card in cards if card["value"] == "ACE")

    # Reduce the value of aces from 11 to 1 as needed
    while total > 21 and ace_count > 0:
        total -= 10 
        ace_count -= 1
    return total


def has_blackjack(cards: List[Dict[str, object]]) -> bool:
    #Return True if the hand total equals 21.
    return hand_total(cards) == 21


def main() -> None:

    check_service_up("https://deckofcardsapi.com/")

    deck_id = get_new_deck()
    shuffle_deck(deck_id)

    cards = deal_cards(deck_id, count=6)
    player1_hand = cards[:3]
    player2_hand = cards[3:]

    print("Player 1 cards:", [card["code"] for card in player1_hand])
    print("Player 2 cards:", [card["code"] for card in player2_hand])

    p1_blackjack = has_blackjack(player1_hand)
    p2_blackjack = has_blackjack(player2_hand)
    if p1_blackjack and p2_blackjack:
        print("Both players have blackjack!")
    elif p1_blackjack:
        print("Player 1 has blackjack!")
    elif p2_blackjack:
        print("Player 2 has blackjack!")
    else:
        print("Neither player has blackjack.")


if __name__ == "__main__":
    main()