import React, { useState } from 'react';

const sauces = [
  { id: 'rest', emoji: '🛏️', name: 'Rest', default: 1.0, tooltip: 'Days since last game. Back-to-backs (0-1 days) hurt performance. 2+ days rest = fresh legs. Bigger rest advantage = bigger edge.' },
  { id: 'defense', emoji: '🛡️', name: 'Defense', default: 1.0, tooltip: 'Defensive efficiency ranking (1-30). Elite defenses (#1-5) force bad shots & turnovers. Poor defenses (#25-30) give up easy buckets.' },
  { id: 'injuries', emoji: '🏥', name: 'Injuries', default: 1.0, tooltip: 'Count of injured players per team. Star injuries (All-NBA) hurt more than bench players. More injuries = weaker team.' },
  { id: 'pace', emoji: '⚡', name: 'Pace', default: 1.0, tooltip: 'Possessions per game. Fast teams (100+) push tempo & score more. Slow teams (96-98) grind it out. Pace mismatches create edges.' },
  { id: 'netRating', emoji: '📊', name: 'Net Rating', default: 1.0, tooltip: 'Points scored minus points allowed per 100 possessions. THE core quality metric. +10 = elite, 0 = average, -10 = tanking.' },
  { id: 'travel', emoji: '✈️', name: 'Travel', default: 1.0, tooltip: 'Miles traveled by away team. Long flights (1500+ mi) cause fatigue. Cross-country trips + time zone changes = sluggish starts.' },
  { id: 'splits', emoji: '🏠', name: 'Home/Away Splits', default: 1.0, tooltip: 'Home vs away win percentages. Some teams dominate at home but struggle on road. Big splits = exploit home/away matchups.' },
  { id: 'rivalry', emoji: '⚔️', name: 'Divisional Rivalry', default: 1.0, tooltip: 'Same-division matchups are more competitive. Teams know each other\'s tendencies. Rivalries = extra intensity & closer games.' },
  { id: 'refs', emoji: '👨‍⚖️', name: 'Ref Bias', default: 1.0, tooltip: 'Home teams get ~2 more FTA/game on average. Some ref crews favor home crowds more. Higher weight = favor home team edge.' },
  { id: 'ftRate', emoji: '🎯', name: 'Free Throw Rate', default: 1.0, tooltip: 'Free throw attempts per field goal attempt. Teams that attack the rim get to the line more. Free points = easy offense.' },
  { id: 'rebounding', emoji: '🏀', name: 'Rebounding', default: 1.0, tooltip: 'Total rebound rate. Offensive rebounds = second-chance points. Defensive rebounds = end opponent possessions. Board control = game control.' },
  { id: 'threePct', emoji: '🎯', name: 'Three-Point %', default: 1.0, tooltip: 'Three-point shooting percentage. Hot shooting nights swing games. Teams shooting 38%+ from three are dangerous. Volume + accuracy = blowouts.' },
];

// Team code mapping for Kalshi tickers
const TEAM_CODES = {
  'Lakers': 'lal', 'Celtics': 'bos', 'Warriors': 'gsw', 'Nuggets': 'den',
  'Heat': 'mia', 'Bucks': 'mil', 'Suns': 'phx', 'Mavericks': 'dal',
  'Clippers': 'lac', 'Knicks': 'nyk', 'Nets': 'bkn', '76ers': 'phi',
  'Bulls': 'chi', 'Cavaliers': 'cle', 'Pistons': 'det', 'Pacers': 'ind',
  'Hawks': 'atl', 'Hornets': 'cha', 'Magic': 'orl', 'Wizards': 'was',
  'Raptors': 'tor', 'Rockets': 'hou', 'Grizzlies': 'mem', 'Pelicans': 'nop',
  'Spurs': 'sas', 'Thunder': 'okc', 'Timberwolves': 'min', 'Trail Blazers': 'por',
  'Jazz': 'uta', 'Kings': 'sac'
};

// Build proper Kalshi URLs
const buildKalshiUrl = (type, awayTeam, homeTeam, line = null) => {
  const date = new Date();
  const dateStr = `${String(date.getFullYear()).slice(2)}jan${String(date.getDate()).padStart(2, '0')}`;
  const awayCode = TEAM_CODES[awayTeam] || awayTeam.toLowerCase().slice(0, 3);
  const homeCode = TEAM_CODES[homeTeam] || homeTeam.toLowerCase().slice(0, 3);
  const ticker = `${dateStr}${awayCode}${homeCode}`;
  
  if (type === 'ML') {
    return `https://kalshi.com/markets/kxnbagame/professional-basketball-game/kxnbagame-${ticker}`;
  } else if (type === 'TOT') {
    return `https://kalshi.com/markets/kxnbatotal/professional-basketball-total/kxnbatotal-${ticker}-o${line?.toString().replace('.', '')}`;
  } else if (type === 'SPR') {
    return `https://kalshi.com/markets/kxnbaspread/professional-basketball-spread/kxnbaspread-${ticker}`;
  }
  return '#';
};

// Sample games with CORRECT ticker association
const sampleGames = [
  { away: 'Lakers', home: 'Celtics', mlEdge: 8.5, totLine: 224.5, totEdge: 6.2, sprLine: -7.5, sprEdge: 4.1, totDir: 'OVER', sprTeam: 'Celtics' },
  { away: 'Warriors', home: 'Nuggets', mlEdge: 5.2, totLine: 228.0, totEdge: 9.1, sprLine: -4.5, sprEdge: 3.8, totDir: 'UNDER', sprTeam: 'Nuggets' },
  { away: 'Heat', home: 'Bucks', mlEdge: 7.8, totLine: 218.5, totEdge: 5.5, sprLine: -6.0, sprEdge: 6.2, totDir: 'OVER', sprTeam: 'Bucks' },
];

const Tooltip = ({ children, text }) => {
  const [show, setShow] = useState(false);
  return (
    <div className="relative inline-block w-full" onMouseEnter={() => setShow(true)} onMouseLeave={() => setShow(false)}>
      {children}
      {show && (
        <div className="absolute z-50 left-full ml-3 top-1/2 -translate-y-1/2 w-64 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-xl border border-gray-700">
          <div className="absolute -left-2 top-1/2 -translate-y-1/2 w-0 h-0 border-t-8 border-b-8 border-r-8 border-transparent border-r-gray-900"></div>
          {text}
        </div>
      )}
    </div>
  );
};

const SauceSlider = ({ sauce, value, onChange }) => (
  <Tooltip text={sauce.tooltip}>
    <div className="mb-3 cursor-help group">
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium text-gray-200 group-hover:text-yellow-400 transition-colors">
          {sauce.emoji} {sauce.name}
        </span>
        <span className="text-xs font-mono bg-gray-700 px-2 py-0.5 rounded text-yellow-400">{value.toFixed(1)}x</span>
      </div>
      <input
        type="range"
        min="0"
        max="2"
        step="0.1"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-yellow-500"
      />
    </div>
  </Tooltip>
);

const EdgeButton = ({ type, game, label, edge, amount, url }) => {
  const colors = {
    ML: 'bg-green-600 hover:bg-green-500',
    TOT: 'bg-blue-600 hover:bg-blue-500',
    SPR: 'bg-purple-600 hover:bg-purple-500'
  };
  
  return (
    <a 
      href={url} 
      target="_blank" 
      rel="noopener noreferrer"
      className={`block w-full ${colors[type]} text-white rounded-lg p-3 transition-all transform hover:scale-102 hover:shadow-lg`}
    >
      <div className="flex justify-between items-center">
        <div>
          <span className="text-xs opacity-75">{type}</span>
          <div className="font-bold">{label}</div>
          <div className="text-xs opacity-75">{game}</div>
        </div>
        <div className="text-right">
          <div className="text-lg font-bold">${amount}</div>
          <div className="text-xs text-green-300">+{edge.toFixed(1)}% edge</div>
        </div>
      </div>
    </a>
  );
};

export default function NBAEdgeFinder() {
  const [weights, setWeights] = useState(
    Object.fromEntries(sauces.map(s => [s.id, s.default]))
  );

  const updateWeight = (id, value) => {
    setWeights(prev => ({ ...prev, [id]: value }));
  };

  const resetAll = () => {
    setWeights(Object.fromEntries(sauces.map(s => [s.id, s.default])));
  };

  return (
    <div className="flex min-h-screen bg-gray-950 text-white">
      {/* LEFT PANEL - ALL 12 SAUCES */}
      <div className="w-80 bg-gray-900 border-r border-gray-800 p-4 overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-yellow-500">🧪 12 SAUCES</h2>
          <button onClick={resetAll} className="text-xs bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded transition-colors">
            Reset All
          </button>
        </div>
        
        <p className="text-xs text-gray-400 mb-4 italic">Hover over any sauce for explanation →</p>

        <div className="space-y-1">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-2 mt-2">Core Factors</div>
          {sauces.slice(0, 6).map(sauce => (
            <SauceSlider
              key={sauce.id}
              sauce={sauce}
              value={weights[sauce.id]}
              onChange={(val) => updateWeight(sauce.id, val)}
            />
          ))}

          <div className="text-xs text-gray-500 uppercase tracking-wider mb-2 mt-4 pt-3 border-t border-gray-700">Advanced Factors</div>
          {sauces.slice(6).map(sauce => (
            <SauceSlider
              key={sauce.id}
              sauce={sauce}
              value={weights[sauce.id]}
              onChange={(val) => updateWeight(sauce.id, val)}
            />
          ))}
        </div>

        <div className="mt-6 p-3 bg-gray-800 rounded-lg border border-gray-700">
          <div className="text-xs text-gray-400 mb-2">Active Weights</div>
          <div className="flex flex-wrap gap-1">
            {sauces.map(s => (
              <span key={s.id} className={`text-xs px-1.5 py-0.5 rounded ${weights[s.id] > 1 ? 'bg-green-900 text-green-400' : weights[s.id] < 1 ? 'bg-red-900 text-red-400' : 'bg-gray-700 text-gray-400'}`}>
                {s.emoji}{weights[s.id].toFixed(1)}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="flex-1 p-6 overflow-y-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-2">🏀 NBA Kalshi Edge Finder</h1>
          <p className="text-gray-400">Adjust your 12 sauces on the left. Click any edge button to bet on Kalshi.</p>
        </div>

        {/* GAMES WITH CLICKABLE EDGES */}
        <div className="space-y-6">
          {sampleGames.map((game, idx) => (
            <div key={idx} className="bg-gray-800 rounded-xl p-5 border border-gray-700">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold">{game.away} @ {game.home}</h3>
                <span className="text-sm text-gray-400">Today</span>
              </div>
              
              <div className="grid grid-cols-3 gap-3">
                {/* MONEYLINE - Links to correct game */}
                <EdgeButton
                  type="ML"
                  game={`${game.away} @ ${game.home}`}
                  label={`🎯 BET ${game.home.toUpperCase()} WINS`}
                  edge={game.mlEdge}
                  amount={Math.round(game.mlEdge * 10)}
                  url={buildKalshiUrl('ML', game.away, game.home)}
                />
                
                {/* TOTALS - Links to correct game with line */}
                <EdgeButton
                  type="TOT"
                  game={`${game.away} @ ${game.home}`}
                  label={`🎯 BET ${game.totDir} ${game.totLine}`}
                  edge={game.totEdge}
                  amount={Math.round(game.totEdge * 10)}
                  url={buildKalshiUrl('TOT', game.away, game.home, game.totLine)}
                />
                
                {/* SPREADS - Links to correct game */}
                <EdgeButton
                  type="SPR"
                  game={`${game.away} @ ${game.home}`}
                  label={`🎯 BET ${game.sprTeam.toUpperCase()} COVERS ${game.sprLine}`}
                  edge={game.sprEdge}
                  amount={Math.round(game.sprEdge * 10)}
                  url={buildKalshiUrl('SPR', game.away, game.home)}
                />
              </div>
            </div>
          ))}
        </div>

        <p className="text-xs text-gray-500 mt-6 text-center">⚠️ For entertainment only. Not financial advice.</p>
      </div>
    </div>
  );
}
