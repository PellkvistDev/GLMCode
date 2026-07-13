const SUITS = ['♠', '♥', '♦', '♣'];
const RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];
const HAND_RANKS = {
    HIGH_CARD: 'High Card',
    PAIR: 'Pair',
    TWO_PAIR: 'Two Pair',
    THREE_OF_A_KIND: 'Three of a Kind',
    STRAIGHT: 'Straight',
    FLUSH: 'Flush',
    FULL_HOUSE: 'Full House',
    FOUR_OF_A_KIND: 'Four of a Kind',
    STRAIGHT_FLUSH: 'Straight Flush',
    ROYAL_FLUSH: 'Royal Flush'
};

const LEARNING_TIPS = {
    preFlop: [
        "Strong starting hands: AA, KK, QQ, JJ, AK, AQ",
        "Suited connectors (e.g., 7♥8♥) have good potential",
        "Avoid marginal hands like 7♣2♦ - they often lead to mistakes",
        "Position matters! Late position gives you more information"
    ],
    flop: [
        "Look for made hands first (pairs, straights)",
        "Connected cards can become straights",
        "Flush draws are powerful - 4 cards of the same suit",
        "Don't overplay weak pairs on wet boards (many suited cards)",
        "Consider your opponents' ranges, not just your hand"
    ],
    turn: [
        "Check your equity - what percentage chance do you have to win?",
        "If you have less than 25% equity, consider folding",
        "If you have 50%+ equity, you can value bet",
        "Position is crucial on the turn - you can see what happens before betting"
    ],
    river: [
        "Trust your read - if you think you're behind, fold",
        "If you have the best hand, bet for value",
        "Consider if your opponent is bluffing based on their actions",
        "Don't overthink - if you have a strong hand, bet it"
    ],
    decisions: [
        "Fold when your hand is unlikely to be best",
        "Check when no one has bet - save money to see more cards",
        "Call to see more cards cheaply when you have equity",
        "Raise to build the pot with your strong hands",
        "Size your bets appropriately - too small = easy to call, too big = might scare players"
    ]
};

class Card {
    constructor(suit, rank) {
        this.suit = suit;
        this.rank = rank;
        this.value = RANKS.indexOf(rank) + 2;
    }

    toString() {
        return `${this.suit}${this.rank}`;
    }

    getColor() {
        return (this.suit === '♥' || this.suit === '♦') ? 'red' : 'black';
    }
}

class Deck {
    constructor() {
        this.cards = [];
        this.reset();
    }

    reset() {
        this.cards = [];
        for (const suit of SUITS) {
            for (const rank of RANKS) {
                this.cards.push(new Card(suit, rank));
            }
        }
        this.shuffle();
    }

    shuffle() {
        for (let i = this.cards.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [this.cards[i], this.cards[j]] = [this.cards[j], this.cards[i]];
        }
    }

    deal() {
        return this.cards.pop();
    }

    remaining() {
        return this.cards.length;
    }
}

class HandEvaluator {
    static evaluate(cards) {
        if (cards.length < 5) {
            return { rank: HAND_RANKS.HIGH_CARD, score: 0, name: HAND_RANKS.HIGH_CARD };
        }

        const allCombinations = this.getCombinations(cards, 5);
        let bestHand = null;
        let bestScore = -1;

        for (const combo of allCombinations) {
            const result = this.evaluateFiveCards(combo);
            if (result.score > bestScore) {
                bestScore = result.score;
                bestHand = result;
            }
        }

        return bestHand;
    }

    static getCombinations(arr, size) {
        if (size === 1) return arr.map(el => [el]);
        const result = [];
        for (let i = 0; i <= arr.length - size; i++) {
            const head = arr[i];
            const tailCombos = this.getCombinations(arr.slice(i + 1), size - 1);
            for (const tail of tailCombos) {
                result.push([head, ...tail]);
            }
        }
        return result;
    }

    static evaluateFiveCards(cards) {
        const sortedCards = [...cards].sort((a, b) => b.value - a.value);
        const values = sortedCards.map(c => c.value);
        const suits = sortedCards.map(c => c.suit);

        const isFlush = suits.every(s => s === suits[0]);
        const isStraight = this.isStraight(values);

        const valueCounts = this.getValueCounts(values);
        const counts = Object.values(valueCounts).sort((a, b) => b - a);

        if (isFlush && isStraight && values[0] === 14) {
            return { rank: HAND_RANKS.ROYAL_FLUSH, score: 900 + values[0], name: HAND_RANKS.ROYAL_FLUSH };
        }

        if (isFlush && isStraight) {
            return { rank: HAND_RANKS.STRAIGHT_FLUSH, score: 800 + values[0], name: HAND_RANKS.STRAIGHT_FLUSH };
        }

        if (counts[0] === 4) {
            const quadValue = parseInt(Object.keys(valueCounts).find(key => valueCounts[key] === 4));
            return { rank: HAND_RANKS.FOUR_OF_A_KIND, score: 700 + quadValue, name: HAND_RANKS.FOUR_OF_A_KIND };
        }

        if (counts[0] === 3 && counts[1] === 2) {
            const tripValue = parseInt(Object.keys(valueCounts).find(key => valueCounts[key] === 3));
            const pairValue = parseInt(Object.keys(valueCounts).find(key => valueCounts[key] === 2));
            return { rank: HAND_RANKS.FULL_HOUSE, score: 600 + tripValue, name: HAND_RANKS.FULL_HOUSE };
        }

        if (isFlush) {
            return { rank: HAND_RANKS.FLUSH, score: 500 + values[0], name: HAND_RANKS.FLUSH };
        }

        if (isStraight) {
            return { rank: HAND_RANKS.STRAIGHT, score: 400 + values[0], name: HAND_RANKS.STRAIGHT };
        }

        if (counts[0] === 3) {
            const tripValue = parseInt(Object.keys(valueCounts).find(key => valueCounts[key] === 3));
            return { rank: HAND_RANKS.THREE_OF_A_KIND, score: 300 + tripValue, name: HAND_RANKS.THREE_OF_A_KIND };
        }

        if (counts[0] === 2 && counts[1] === 2) {
            const pairs = Object.keys(valueCounts).filter(key => valueCounts[key] === 2).map(Number).sort((a, b) => b - a);
            return { rank: HAND_RANKS.TWO_PAIR, score: 200 + pairs[0] * 100 + pairs[1], name: HAND_RANKS.TWO_PAIR };
        }

        if (counts[0] === 2) {
            const pairValue = parseInt(Object.keys(valueCounts).find(key => valueCounts[key] === 2));
            return { rank: HAND_RANKS.PAIR, score: 100 + pairValue, name: HAND_RANKS.PAIR };
        }

        return { rank: HAND_RANKS.HIGH_CARD, score: values[0], name: HAND_RANKS.HIGH_CARD };
    }

    static isStraight(values) {
        const sorted = [...values].sort((a, b) => a - b);
        if (sorted[4] - sorted[0] === 4 && new Set(sorted).size === 5) return true;
        if (sorted.join(',') === '2,3,4,5,14') return true;
        return false;
    }

    static getValueCounts(values) {
        const counts = {};
        for (const v of values) {
            counts[v] = (counts[v] || 0) + 1;
        }
        return counts;
    }

    static getHandStrength(cards, communityCards) {
        const allCards = [...cards, ...communityCards];
        const hand = this.evaluate(allCards);
        return hand.score;
    }
}

class AIPlayer {
    constructor(name, stack, aggression = 0.5, tightness = 0.5) {
        this.name = name;
        this.stack = stack;
        this.aggression = aggression;
        this.tightness = tightness;
        this.handHistory = [];
        this.vpip = 0;
        this.pfr = 0;
    }

    updateStats(action, handStrength) {
        this.handHistory.push({ action, handStrength, position: 'unknown' });
        if (this.handHistory.length > 100) this.handHistory.shift();

        const vpipCount = this.handHistory.filter(h => h.action === 'call' || h.action === 'raise').length;
        this.vpip = vpipCount / this.handHistory.length;

        const pfrCount = this.handHistory.filter(h => h.action === 'raise').length;
        this.pfr = pfrCount / this.handHistory.length;
    }

    decide(playerCards, communityCards, pot, currentBet, toCall, position) {
        const handStrength = HandEvaluator.getHandStrength(playerCards, communityCards);
        const equity = this.calculateEquity(playerCards, communityCards);

        const random = Math.random();
        const positionFactor = position === 'late' ? 0.1 : position === 'early' ? -0.1 : 0;

        let foldThreshold = 0.3 + (this.tightness * 0.4) + positionFactor;
        let bluffThreshold = 0.6 - (this.aggression * 0.3) + positionFactor;
        let valueRaiseThreshold = 0.5 + (this.aggression * 0.3) + positionFactor;

        if (handStrength > valueRaiseThreshold) {
            return { action: 'raise', amount: this.calculateRaiseAmount(pot, toCall) };
        }

        if (handStrength > foldThreshold) {
            if (random < bluffThreshold) {
                return { action: 'raise', amount: this.calculateRaiseAmount(pot, toCall) };
            }
            return { action: 'call', amount: toCall };
        }

        if (equity > 0.3 && random < 0.3) {
            return { action: 'call', amount: toCall };
        }

        return { action: 'fold', amount: 0 };
    }

    calculateEquity(playerCards, communityCards) {
        const allCards = [...playerCards, ...communityCards];
        if (allCards.length < 2) return 0.5;

        const deck = new Deck();
        deck.cards = deck.cards.filter(c => !allCards.includes(c));

        let wins = 0;
        let ties = 0;

        const remainingCombinations = deck.remaining() >= 5 ? deck.remaining() - 4 : 0;

        for (let i = 0; i < Math.min(remainingCombinations, 1000); i++) {
            const community = [...communityCards];
            while (community.length < 5) {
                community.push(deck.deal());
            }
            const playerHand = HandEvaluator.evaluate(playerCards);
            const comboHand = HandEvaluator.evaluate(community);

            if (playerHand.score > comboHand.score) wins++;
            else if (playerHand.score === comboHand.score) ties++;
        }

        return (wins + ties / 2) / Math.min(remainingCombinations, 1000);
    }

    calculateRaiseAmount(pot, toCall) {
        const minRaise = toCall + 10;
        const maxRaise = this.stack;
        const raiseSize = minRaise + Math.floor(Math.random() * (maxRaise - minRaise));
        return Math.min(raiseSize, maxRaise);
    }

    getOpponentStyle() {
        if (this.vpip > 0.5) return 'Loose';
        if (this.vpip < 0.3) return 'Tight';
        if (this.pfr > 0.3) return 'Aggressive';
        return 'Passive';
    }
}

class Game {
    constructor() {
        this.deck = new Deck();
        this.player = { cards: [], stack: 1000, name: 'You' };
        this.opponents = [
            new AIPlayer('Alex', 500, 0.6, 0.4),
            new AIPlayer('Sarah', 500, 0.4, 0.6),
            new AIPlayer('Mike', 500, 0.5, 0.5)
        ];
        this.communityCards = [];
        this.pot = 0;
        this.currentBet = 0;
        this.handsPlayed = 0;
        this.wins = 0;
        this.gameState = 'preFlop';
        this.currentPlayer = 0;
        this.dealerPosition = 0;
        this.learningTips = [];
        this.handPhase = 'preFlop';
        this.lastAction = null;
    }

    startNewGame() {
        this.deck.reset();
        this.player.cards = [this.deck.deal(), this.deck.deal()];
        this.communityCards = [];
        this.pot = 0;
        this.currentBet = 0;
        this.gameState = 'preFlop';
        this.handPhase = 'preFlop';
        this.currentPlayer = (this.dealerPosition + 1) % 4;
        this.learningTips = [];

        const smallBlind = 10;
        const bigBlind = 20;

        for (let i = 0; i < 4; i++) {
            this.opponents[i].stack = 500;
        }

        this.placeBet(this.currentPlayer, smallBlind);
        this.placeBet((this.currentPlayer + 1) % 4, bigBlind);
        this.currentBet = bigBlind;

        this.handsPlayed++;
        this.updateStats();
        this.render();
        this.showLearningTip('preFlop', this.player.cards);
    }

    placeBet(playerIndex, amount) {
        const player = playerIndex === 0 ? this.player : this.opponents[playerIndex - 1];
        const actualAmount = Math.min(amount, player.stack);

        player.stack -= actualAmount;
        this.pot += actualAmount;
        this.currentBet = Math.max(this.currentBet, actualAmount);

        if (playerIndex === 0) {
            this.lastAction = { player: 'You', action: 'bet', amount: actualAmount };
        } else {
            const opponent = this.opponents[playerIndex - 1];
            this.lastAction = { player: opponent.name, action: 'bet', amount: actualAmount };
        }
    }

    playerAction(action, amount = 0) {
        if (this.currentPlayer !== 0 || this.gameState === 'ended') return;

        const toCall = this.currentBet - this.getBetForPlayer(0);

        if (action === 'fold') {
            this.endHand('opponents');
            return;
        }

        if (action === 'check' && toCall > 0) return;

        if (action === 'call') {
            this.placeBet(0, toCall);
            this.updateAIStats(0, 'call');
        }

        if (action === 'raise') {
            const raiseAmount = Math.min(amount, this.player.stack);
            this.placeBet(0, raiseAmount + toCall);
            this.updateAIStats(0, 'raise');
        }

        this.currentPlayer = (this.currentPlayer + 1) % 4;

        if (this.allPlayersActed()) {
            this.nextPhase();
        } else {
            this.render();
            this.showLearningCue();
        }
    }

    getBetForPlayer(playerIndex) {
        if (playerIndex === 0) return this.player.stack;
        return this.opponents[playerIndex - 1].stack;
    }

    allPlayersActed() {
        const actedPlayers = new Set();
        for (let i = 0; i < 4; i++) {
            const player = i === 0 ? this.player : this.opponents[i - 1];
            if (player.stack === 0) continue;
            if (i === this.currentPlayer) continue;

            const toCall = this.currentBet - this.getBetForPlayer(i);
            if (toCall === 0 && !this.hasRaisedSince(i)) continue;

            actedPlayers.add(i);
        }

        return actedPlayers.size === 3;
    }

    hasRaisedSince(playerIndex) {
        const startPlayer = (this.currentPlayer + 1) % 4;
        for (let i = startPlayer; i !== playerIndex; i = (i + 1) % 4) {
            const player = i === 0 ? this.player : this.opponents[i - 1];
            if (player.stack === 0) continue;
            if (this.getBetForPlayer(i) > this.getBetForPlayer(startPlayer)) {
                return true;
            }
        }
        return false;
    }

    updateAIStats(playerIndex, action) {
        if (playerIndex === 0) return;
        const opponent = this.opponents[playerIndex - 1];
        const handStrength = HandEvaluator.getHandStrength(this.player.cards, this.communityCards);
        opponent.updateStats(action, handStrength);
    }

    nextPhase() {
        this.currentBet = 0;
        this.currentPlayer = (this.dealerPosition + 1) % 4;

        if (this.gameState === 'preFlop') {
            this.gameState = 'flop';
            this.communityCards = [this.deck.deal(), this.deck.deal(), this.deck.deal()];
            this.handPhase = 'flop';
            this.showLearningTip('flop', this.player.cards);
        } else if (this.gameState === 'flop') {
            this.gameState = 'turn';
            this.communityCards.push(this.deck.deal());
            this.handPhase = 'turn';
            this.showLearningTip('turn', this.player.cards);
        } else if (this.gameState === 'turn') {
            this.gameState = 'river';
            this.communityCards.push(this.deck.deal());
            this.handPhase = 'river';
            this.showLearningTip('river', this.player.cards);
        } else if (this.gameState === 'river') {
            this.determineWinner();
            return;
        }

        this.render();
        this.showLearningCue();
    }

    determineWinner() {
        const playerHand = HandEvaluator.evaluate([...this.player.cards, ...this.communityCards]);
        const bestOpponent = this.findBestOpponentHand();

        if (playerHand.score > bestOpponent.score) {
            this.endHand('player', playerHand);
        } else if (playerHand.score < bestOpponent.score) {
            this.endHand('opponents', playerHand);
        } else {
            this.endHand('tie', playerHand);
        }
    }

    findBestOpponentHand() {
        let bestScore = -1;
        let bestHand = null;

        for (let i = 0; i < 3; i++) {
            const hand = HandEvaluator.evaluate([...this.opponents[i].cards, ...this.communityCards]);
            if (hand.score > bestScore) {
                bestScore = hand.score;
                bestHand = hand;
            }
        }

        return bestHand;
    }

    endHand(result, playerHand) {
        this.gameState = 'ended';

        if (result === 'player') {
            this.player.stack += this.pot;
            this.wins++;
            this.showLearningTip('win', playerHand);
        } else if (result === 'opponents') {
            for (let i = 0; i < 3; i++) {
                this.opponents[i].stack += this.pot / 3;
            }
            this.showLearningTip('lose', playerHand);
        } else {
            this.player.stack += this.pot / 2;
            for (let i = 0; i < 3; i++) {
                this.opponents[i].stack += this.pot / 6;
            }
            this.showLearningTip('tie', playerHand);
        }

        this.pot = 0;
        this.dealerPosition = (this.dealerPosition + 1) % 4;
        this.updateStats();
        this.render();
    }

    showLearningTip(phase, playerCards) {
        const tips = LEARNING_TIPS[phase] || [];
        const relevantTip = tips[Math.floor(Math.random() * tips.length)];
        this.learningTips.unshift({ phase, tip: relevantTip, time: Date.now() });
        if (this.learningTips.length > 10) this.learningTips.pop();
    }

    showLearningCue() {
        const cue = document.getElementById('learningCue');
        const toCall = this.currentBet - this.getBetForPlayer(0);
        const handStrength = HandEvaluator.getHandStrength(this.player.cards, this.communityCards);

        let cueText = '';
        if (this.gameState === 'ended') return;

        if (toCall > 0) {
            cueText = `You need to call $${toCall} to continue`;
        } else {
            cueText = 'You can check or raise';
        }

        if (handStrength > 400) {
            cueText += ' - Strong hand! Consider value betting';
        } else if (handStrength > 200) {
            cueText += ' - Decent hand, proceed carefully';
        } else {
            cueText += ' - Weak hand, consider folding';
        }

        cue.innerHTML = cueText;
    }

    updateStats() {
        document.getElementById('bankroll').textContent = `$${this.player.stack}`;
        document.getElementById('handsPlayed').textContent = this.handsPlayed;
        const winRate = this.handsPlayed > 0 ? ((this.wins / this.handsPlayed) * 100).toFixed(1) : 0;
        document.getElementById('winRate').textContent = `${winRate}%`;
    }

    render() {
        this.renderPlayerCards();
        this.renderOpponentCards();
        this.renderCommunityCards();
        this.renderPot();
        this.renderCurrentBet();
        this.renderHandRank();
        this.renderOpponentStatus();
        this.renderControls();
        this.renderLearningTips();
        this.updateStats();
    }

    renderPlayerCards() {
        const container = document.getElementById('playerCards');
        container.innerHTML = this.player.cards.map(card => this.createCardElement(card)).join('');
    }

    renderOpponentCards() {
        for (let i = 0; i < 3; i++) {
            const container = document.getElementById(`opponent${i + 1}-cards`);
            const opponent = this.opponents[i];
            const cards = opponent.cards.map(card => this.createCardElement(card));
            container.innerHTML = opponent.folded ? '' : cards.join('');
        }
    }

    renderCommunityCards() {
        const container = document.getElementById('communityCards');
        container.innerHTML = this.communityCards.map(card => this.createCardElement(card)).join('');
    }

    createCardElement(card) {
        return `
            <div class="card ${card.getColor()}" data-suit="${card.suit}" data-rank="${card.rank}">
                <div class="card-value">${card.rank}</div>
                <div class="card-suit">${card.suit}</div>
            </div>
        `;
    }

    renderPot() {
        document.getElementById('potAmount').textContent = `$${this.pot}`;
    }

    renderCurrentBet() {
        const toCall = this.currentBet - this.getBetForPlayer(0);
        document.getElementById('currentBet').textContent = toCall > 0 ? `Current bet: $${toCall}` : '';
    }

    renderHandRank() {
        const hand = HandEvaluator.evaluate([...this.player.cards, ...this.communityCards]);
        document.getElementById('handRank').textContent = hand.name;
        document.getElementById('handRank').style.color = this.getHandColor(hand.score);
    }

    getHandColor(score) {
        if (score >= 800) return '#ffd700';
        if (score >= 600) return '#4ade80';
        if (score >= 400) return '#60a5fa';
        if (score >= 300) return '#a78bfa';
        if (score >= 200) return '#f472b6';
        if (score >= 100) return '#fbbf24';
        return '#9ca3af';
    }

    renderOpponentStatus() {
        for (let i = 0; i < 3; i++) {
            const status = document.getElementById(`opponent${i + 1}-status`);
            const opponent = this.opponents[i];

            if (opponent.stack === 0) {
                status.textContent = 'All-in';
            } else if (this.gameState === 'ended') {
                const hand = HandEvaluator.evaluate([...opponent.cards, ...this.communityCards]);
                status.textContent = hand.name;
            } else {
                status.textContent = '';
            }
        }
    }

    renderControls() {
        const toCall = this.currentBet - this.getBetForPlayer(0);
        const canCheck = toCall === 0;

        document.getElementById('foldBtn').disabled = this.currentPlayer !== 0 || this.gameState === 'ended';
        document.getElementById('checkBtn').disabled = !canCheck || this.currentPlayer !== 0 || this.gameState === 'ended';
        document.getElementById('callBtn').disabled = canCheck || this.currentPlayer !== 0 || this.gameState === 'ended';
        document.getElementById('raiseBtn').disabled = this.currentPlayer !== 0 || this.gameState === 'ended';

        const raiseAmount = Math.min(parseInt(document.getElementById('raiseAmount').value) || 20, this.player.stack);
        document.getElementById('raiseAmount').max = this.player.stack;
        document.getElementById('raiseAmount').value = Math.max(raiseAmount, 20);
    }

    renderLearningTips() {
        const container = document.getElementById('learningTips');
        container.innerHTML = this.learningTips.map(tip => `
            <div class="tip ${tip.phase === 'win' ? 'hint' : tip.phase === 'lose' ? 'warning' : ''}">
                <strong>${tip.phase.toUpperCase()}:</strong> ${tip.tip}
            </div>
        `).join('');
    }
}

const game = new Game();

document.getElementById('newGameBtn').addEventListener('click', () => {
    game.startNewGame();
});

document.getElementById('foldBtn').addEventListener('click', () => {
    game.playerAction('fold');
});

document.getElementById('checkBtn').addEventListener('click', () => {
    game.playerAction('check');
});

document.getElementById('callBtn').addEventListener('click', () => {
    const toCall = game.currentBet - game.getBetForPlayer(0);
    game.playerAction('call', toCall);
});

document.getElementById('raiseBtn').addEventListener('click', () => {
    const raiseAmount = parseInt(document.getElementById('raiseAmount').value) || 20;
    game.playerAction('raise', raiseAmount);
});

document.getElementById('raiseAmount').addEventListener('change', () => {
    game.renderControls();
});

game.startNewGame();
