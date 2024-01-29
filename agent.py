from abc import ABC, abstractmethod
from collections import defaultdict
from card import Card


class HeartsAgent(ABC):
    NUM_AGENTS = 4

    """
    @param agent_id
    @param cards a list of `Card` corresponding to the cards in the hand of this agent.
    """
    @abstractmethod
    def __init__(self, agent_id, cards):
        pass

    """
    @returns action agent would take.
    """
    @abstractmethod
    def getNextAction(self):
        pass

    """
    @description called when any agent takes an action (including this one).
    """
    @abstractmethod
    def observeActionTaken(self, agent_id, card):
        pass

    """
    @description called when any agent needs to reset seen cards    
    """
    @abstractmethod
    def resetSeenCards(self):
        pass


class SimpleHeartsAgent(HeartsAgent):
    def __init__(self, agent_id, cards):
        self.agent_id = agent_id
        self.in_play = []
        self.card_map = defaultdict(list)
        for card in cards:
            self.card_map[card.suit].append(card)
            
    def getNextAction(self):
        if len(self.in_play) == 0:
            for _, cards in self.card_map.items():
                if len(cards) > 0:
                    return cards[-1]
        
        # if there's a leading suit, play the last card (for efficiency) with the same suit as the leading suit.
        if len(self.in_play) > 0:
            leading_suit = self.in_play[0].suit
            if len(self.card_map[leading_suit]) > 0:
                return self.card_map[leading_suit][-1]

        # New rules implementation when the agent cannot follow the leading suit
        jack_of_spades = Card(Card.Suit.SPADES, 11)
        if jack_of_spades in self.card_map[Card.Suit.SPADES]:
            # Rule 1: Play the Jack of Spades if available
            return jack_of_spades
        elif len(self.card_map[Card.Suit.HEARTS]) > 0:
            # Rule 2: If Jack of Spades is not available, play a card from Hearts
            return self.card_map[Card.Suit.HEARTS][-1]
        else:
            # Rule 3: If neither Jack of Spades nor Hearts are available, play any card
            for _, cards in self.card_map.items():
                if len(cards) > 0:
                    return cards[-1]

        
                
        # This should not normally happen, as the agent should always have cards to play
        raise RuntimeError(f"Agent {self.agent_id} does not have any remaining cards to play.")

    
    def observeActionTaken(self, agent_id, card):
        if self.agent_id == agent_id:
            # since this agent's action should be the last element from this list, this should be a constant operation.
            self.card_map[card.suit].remove(card)
        self.in_play.append(card)
        if len(self.in_play) == self.NUM_AGENTS:
            self.in_play.clear()

    def resetSeenCards(self):
        pass


class MDPHeartsAgent(HeartsAgent):
    def __init__(self, agent_id, cards, getSeen, get_next_action_fn, observe_action_taken_fn):
        self.agent_id = agent_id
        self.in_play = []
        print(f"\033[1mAI hand:\033[0m") #Bold
        for card in cards:
            print((card.num, card.suit))
        self.cards = set(cards)
        self.getSeen = getSeen
        self.get_next_action_fn = get_next_action_fn
        self.observe_action_taken_fn = observe_action_taken_fn

    def getNextAction(self):
        remaining_moves = (self.NUM_AGENTS - 1) - len(self.in_play)
        leading_suit = Card.Suit.getSuitShortStr(
            self.in_play[0].suit) if len(self.in_play) > 0 else "none"

        player_cards = []
        for i in range(Card.NUM_CARDS):
            card = Card.createFromCardIdx(i)
            if card in self.in_play:
                player_cards.append("in_play")
            elif f"{card.num}{Card.Suit.getSuitShortStr(card.suit)}" in self.getSeen():
                player_cards.append("seen")
            elif card in self.cards:
                player_cards.append("m1")
                continue
            else:
                player_cards.append("m2")
        action_str = self.get_next_action_fn(
            remaining_moves, leading_suit, player_cards)
        suit = Card.Suit.getShortStrSuit(action_str[-1])
        mdp_card = Card(suit, int(action_str[:-1]))
        if mdp_card not in self.cards:
            raise Exception(
                f"was not able to find mdp_card: ({mdp_card.suit},{mdp_card.num}) in cards: {self.cards})")
            # choose a random card to essentially penalize for making an incorrect decision
            # return next(iter(self.cards))
        #print(
            #f"AI played {str(mdp_card)}")
            #f"AI played {str(mdp_card)}")
        return mdp_card

    def observeActionTaken(self, agent_id, card):
        print(
            f"Agent {agent_id} played {card.num} of {card.suit}")
        self.observe_action_taken_fn(
            f"{card.num}{Card.Suit.getSuitShortStr(card.suit)}")

        if self.agent_id == agent_id:
            self.cards.remove(card)
        self.in_play.append(card)
        if len(self.in_play) == self.NUM_AGENTS:
            self.in_play.clear()

    def resetSeenCards(self):
        self.observe_action_taken_fn("reset")
