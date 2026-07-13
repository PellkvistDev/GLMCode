# Texas Hold'em Learning Simulator

A fully client-side Texas Hold'em poker simulator designed for learning. Features smart AI opponents, learning cues, and detailed statistics tracking.

## Features

- **Smart AI Opponents**: Three opponents with different playing styles (tight/loose, aggressive/passive)
- **Learning System**: Contextual tips and cues that appear during your turn
- **Statistics Tracking**: Monitor bankroll, hands played, and win rate
- **Hand Evaluation**: Real-time hand strength and rank display
- **Position Awareness**: Late position gives you more information

## How to Play

1. Click "New Game" to start a hand
2. Review the learning tips that appear during each phase
3. Use the buttons to Fold, Check, Call, or Raise
4. Watch your opponents make decisions based on their hand strength
5. Track your win rate and bankroll over time

## Learning Tips

The simulator provides context-specific tips:

- **Pre-flop**: Learn about strong starting hands and position importance
- **Flop**: Understand board texture and hand potential
- **Turn**: Evaluate your equity and make informed decisions
- **River**: Trust your reads and make final decisions

## Deployment

This is a single-page application that runs entirely in the browser:

1. Push to your GitHub repository
2. Connect to Render (free tier)
3. Select "Static Site" deployment
4. Render will automatically build and deploy your site

## Technical Details

- Pure JavaScript (no frameworks)
- CSS for styling
- Responsive design for all screen sizes
- No server-side code required
