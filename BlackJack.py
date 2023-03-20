import random
import sys
import sqlite3
from tabulate import tabulate

# Checks the database if the leaderboard is already made, if not create the leaderboard
# Table will be used to store player's score (amount of money)
connection = sqlite3.connect('BlackJack.db')
c = connection.cursor()
c.execute("SELECT COUNT(*) FROM sqlite_schema WHERE type = 'table' AND name = 'leaderboard' ")
tableExist = c.fetchone()[0]
if tableExist == 0:
    c.execute('CREATE TABLE leaderboard (id INT PRIMARY KEY NOT NULL,username TEXT NOT NULL, score INT NOT NULL)')
connection.commit()

# If table is empty, add some dummy scores
c.execute('SELECT COUNT(id) FROM leaderboard')
playerID = c.fetchone()[0]
if playerID == 0:
    c.execute("INSERT INTO leaderboard (id, username, score) VALUES ('00', 'lorem', '1300')")
    c.execute("INSERT INTO leaderboard (id, username, score) VALUES ('01', 'ipsum', '2200')")
    c.execute("INSERT INTO leaderboard (id, username, score) VALUES ('02', 'dolor', '30')")
    c.execute("INSERT INTO leaderboard (id, username, score) VALUES ('03', 'sit', '0')")
    c.execute("INSERT INTO leaderboard (id, username, score) VALUES ('04', 'amet', '400')")

# Create constants used for the cards
HEARTS = chr(9829)
SPADES = chr(9824)
DIAMONDS = chr(9830)
CLUBS = chr(9827)
BACKSIDE = 'backside'


def main():
    print('Welcome to BlackJack!')
    print('''Objective: Each participant attempts to beat the dealer by getting a count as close to 21 as possible, 
    without going over 21''')
    print('''Rules: Face cards are worth 10 and an ace is either 1 or 11, any other card is its numerical value. 
    In this game, it will be automate the best value for ace based on your hand. Each player is given two cards and is 
    able to either "Hit" for another card in order to get closer to 21 or exactly 21, "Stand" to keep your current 
    hand, and only when you have exactly two cards can you "Double-down" to place an additional bet equal to or less 
    than your current bet to get one card followed by standing. If you exceed 21, then you bust and lose. If you get 
    21 in exactly two cards, it is a BlackJack! and you win 1.5x your bet.''')
    print('Good luck and happy betting!\n')
    # Generate starting money(score) and unique playerID
    money = 1000
    c.execute('SELECT COUNT(id) FROM leaderboard')
    playerID = c.fetchone()[0]
    playerID += 1
    # Display current leaderboard (Top 10 scores)
    c.execute('SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 10')
    scoreboard = c.fetchall()
    print('LEADERBOARDS:')
    print(tabulate(scoreboard, headers=('Username', 'Score')))

    while True:  # The game loop
        # Check current balance
        if money <= 0:
            print("You ran out of money. Better luck next time!")
            # Enter username into leaderboard then show leader board
            username = input('What username would you like to use for the leaderboard: ')
            c.execute('INSERT INTO leaderboard (id, username, score) VALUES (?, ?, ?)', (playerID, username, money))
            connection.commit()
            c.execute('SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 10')
            scoreboard = c.fetchall()
            print('LEADERBOARDS:')
            print(tabulate(scoreboard, headers=('Username', 'Score')))
            connection.commit()
            connection.close()
            print('Thanks for playing!')
            sys.exit()
        # Enter bet amount
        print('Balance: $', money)
        bet = getBet(money, playerID)
        # Deal cards: two to player, two to dealer with one backside (not revealed)
        deck = getDeck()
        dealerHand = [deck.pop(), deck.pop()]
        playerHand = [deck.pop(), deck.pop()]
        # Get player input (Hit, Stand, Double-down)
        while True:
            displayHand(playerHand, dealerHand, False)
            print()
            # Check if player has 21
            if getHand(playerHand) == 21:
                break
            # Check if player busted
            if getHand(playerHand) > 21:
                break
            # Get player input (Hit, Stand, Double-down)
            move = getInput(playerHand, money - bet)
            # Handle player's input (Hit, Stand, Double-down)
            if move == '3':
                additionalBet = getBet(min(bet, (money - bet)))
                bet += additionalBet
                print('Bet increased to {}'.format(bet))
                print('Bet:', bet)
                newCard = deck.pop()
                face, suit = newCard
                print('You drew a {} of {}'.format(face, suit))
                playerHand.append(newCard)
                break
            if move == '2':
                break
            if move == '1':
                newCard = deck.pop()
                face, suit = newCard
                print('You drew a {} of {}'.format(face, suit))
                playerHand.append(newCard)
        # Handle dealer actions
        if getHand(playerHand) <= 21:
            while getHand(dealerHand) < 17:
                print('Dealer hits.')
                dealerHand.append(deck.pop())
                displayHand(playerHand, dealerHand, False)
                if getHand(dealerHand) > 21:
                    break
                input('Press ENTER to continue:')
                print('\n')
        # Show the final hand
        displayHand(playerHand, dealerHand, True)
        # Handle all possible outcomes
        playerValue = getHand(playerHand)
        dealerValue = getHand(dealerHand)
        # Win conditions
        if (playerValue == 21 and len(playerHand) == 2) and not (dealerValue == 21 and len(dealerHand) == 2):
            # Win by BlackJack
            print('BlackJack! You WIN ${}!'.format(bet * 1.5))
            money += (bet * 1.5)
        elif dealerValue > 21 >= playerValue:
            # Win by dealer bust
            print('Dealer busts. You WIN ${}!'.format(bet))
            money += bet
        elif 21 >= playerValue > dealerValue:
            # Win by hand > dealer hand
            print('You WIN ${}!'.format(bet))
            money += bet
        # Lose conditions
        elif (dealerValue == 21 and len(dealerHand) == 2) and not (playerValue == 21 and len(playerHand) == 2):
            # Lose by dealer BlackJack
            print('Dealer BlackJack! You LOSE!')
            money -= bet
        elif playerValue > 21:
            # Lose by bust
            print('You busted! You LOSE!')
            money -= bet
        elif 21 >= dealerValue > playerValue:
            # Lose by dealer hand > hand
            print('Dealer wins! You LOSE!')
            money -= bet
        # Tie condition
        elif 21 >= playerValue == dealerValue:
            # Tie by same hand value
            print('Push! You tied!')
        elif (playerValue == 21 and len(playerHand) == 2) and (dealerValue == 21 and len(dealerHand) == 2):
            # Tie by both BlackJack
            print('Push! You tied!')

        input('Press ENTER to continue:')
        print('\n')


def getBet(maxBet, userID):
    # Ask player for amount to bet
    while True:  # Keep asking until user inputs a valid amount
        print('How much do you bet? (1-{}, or QUIT)'.format(maxBet))
        bet = input('> ').upper().strip()
        if bet == 'QUIT':
            print('Thanks for Playing!')
            username = input('What username would you like to use for the leaderboard: ')
            score = maxBet
            c.execute('INSERT INTO leaderboard (id, username, score) VALUES (?, ?, ?)', (userID, username, score))
            connection.commit()
            c.execute('SELECT username, score FROM leaderboard ORDER BY score DESC LIMIT 10')
            scoreboard = c.fetchall()
            print('LEADERBOARDS:')
            print(tabulate(scoreboard, headers=('Username', 'Score')))
            connection.close()
            sys.exit()
        if not bet.isdecimal():
            continue
        bet = int(bet)
        if 1 <= bet <= maxBet:
            return bet


def getDeck():
    # Return a list of tuples for all 52 cards
    deck = []
    for suit in (HEARTS, SPADES, DIAMONDS, CLUBS):
        for face in range(2, 11):
            deck.append((str(face), suit))  # Adds numbered cards to deck
        for face in ('J', 'Q', 'K', 'A'):
            deck.append((face, suit))  # Adds face cards to deck
    random.shuffle(deck)
    return deck


def displayHand(playerHand, dealerHand, showDealerHand):
    # shows the players and dealers hands hide the dealers first card if showdealerhand is false
    print()
    if showDealerHand:
        print('DEALER:', getHand(dealerHand))
        displayCards(dealerHand)
    else:
        print('DEALER: ???')
        displayCards([BACKSIDE] + dealerHand[1:])

    print('PLAYER:', getHand(playerHand))
    displayCards(playerHand)


def getHand(cards):
    value = 0
    numAces = 0
    for card in cards:
        face = card[0]
        if face == 'A':
            numAces += 1
        elif face in ('J', 'Q', 'K'):
            value += 10
        else:
            value += int(face)
    value += numAces
    for i in range(numAces):
        if value + 10 < 21:
            value += 10
    return value


def displayCards(cards):
    rows = ['', '', '', '']
    for i, card in enumerate(cards):
        rows[0] += ' ___ '
        if card == BACKSIDE:
            rows[1] += '|?  |'
            rows[2] += '| ? |'
            rows[3] += '|__?|'
        else:
            face, suit = card
            rows[1] += '|{} |'.format(face.ljust(2))
            rows[2] += '| {} |'.format(suit)
            rows[3] += '|_{}|'.format(face.rjust(2, '_'))
    for row in rows:
        print(row)


def getInput(playerHand, money):
    actions = ['1: Hit', '2: Stand']
    if len(playerHand) == 2 and money > 0:
        actions.append('3: Double-down')
    for action in actions:
        print(action)
    move = input('> ').upper().strip()
    if move in ('1', '2'):
        return move
    if move == '3' and '3: Double-down' in actions:
        return move


if __name__ == '__main__':
    main()