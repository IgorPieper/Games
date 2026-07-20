
import React, { useEffect, useRef, useState } from 'react';
import {
  Modal,
  Pressable,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const SAVE_KEY = 'cactus_clicker_snack_v7';

const DEFAULT_UPGRADES = {
  click: 0,
  auto: 0,
  fertilizer: 0,
  critChance: 0,
  critPower: 0,
  combo: 0,
  xp: 0,
  crystals: 0,
};

const DEFAULT_RESEARCH = {
  click: 0,
  auto: 0,
  xp: 0,
  luck: 0,
};

const DEFAULT_BIOME_LEVELS = {
  garden: 0,
  desert: 0,
  canyon: 0,
  moon: 0,
  nebula: 0,
};

const SKINS = [
  {
    id: 'saguaro',
    species: 'saguaro',
    name: 'Saguaro',
    subtitle: 'Carnegiea gigantea',
    level: 1,
    price: 0,
    bonus: 1,
    body: '#46A857',
    bodyDark: '#267338',
    bodyLight: '#8DDD98',
    pot: '#A86039',
    accent: '#F1D17B',
  },
  {
    id: 'barrel',
    species: 'barrel',
    name: 'Kaktus beczkowy',
    subtitle: 'Echinocactus grusonii',
    level: 4,
    price: 8,
    bonus: 1.05,
    body: '#5AAE4B',
    bodyDark: '#2F7633',
    bodyLight: '#9AD98E',
    pot: '#A65F39',
    accent: '#F4D35E',
  },
  {
    id: 'bunny',
    species: 'bunny',
    name: 'Uszy królika',
    subtitle: 'Opuntia microdasys',
    level: 7,
    price: 18,
    bonus: 1.1,
    body: '#67B95B',
    bodyDark: '#377C3B',
    bodyLight: '#A9E09F',
    pot: '#C27645',
    accent: '#F3E2A9',
  },
  {
    id: 'moon',
    species: 'moon',
    name: 'Kaktus księżycowy',
    subtitle: 'Gymnocalycium mihanovichii',
    level: 11,
    price: 35,
    bonus: 1.17,
    body: '#3C9A50',
    bodyDark: '#216834',
    bodyLight: '#7FCB8E',
    pot: '#61504A',
    accent: '#F25F5C',
  },
  {
    id: 'oldman',
    species: 'oldman',
    name: 'Kaktus starzec',
    subtitle: 'Cephalocereus senilis',
    level: 16,
    price: 65,
    bonus: 1.28,
    body: '#4F9B55',
    bodyDark: '#2A6933',
    bodyLight: '#A8D5A9',
    pot: '#8C6045',
    accent: '#F2F1E8',
  },
  {
    id: 'aloe',
    species: 'aloe',
    name: 'Aloes zwyczajny',
    subtitle: 'Aloe vera',
    level: 20,
    price: 95,
    bonus: 1.38,
    body: '#4FAE63',
    bodyDark: '#286E3D',
    bodyLight: '#90D49B',
    pot: '#B06C42',
    accent: '#DDE8B2',
  },
  {
    id: 'haworthia',
    species: 'haworthia',
    name: 'Haworsja pasiasta',
    subtitle: 'Haworthiopsis attenuata',
    level: 25,
    price: 140,
    bonus: 1.52,
    body: '#2F7F45',
    bodyDark: '#174F2C',
    bodyLight: '#62B879',
    pot: '#756054',
    accent: '#E8F1D5',
  },
  {
    id: 'echeveria',
    species: 'echeveria',
    name: 'Eszeweria',
    subtitle: 'Echeveria elegans',
    level: 30,
    price: 210,
    bonus: 1.7,
    body: '#83B9A2',
    bodyDark: '#527F6C',
    bodyLight: '#C0DED1',
    pot: '#B57C5A',
    accent: '#EAD8E7',
  },
  {
    id: 'lithops',
    species: 'lithops',
    name: 'Żywe kamienie',
    subtitle: 'Lithops aucampiae',
    level: 38,
    price: 320,
    bonus: 1.95,
    body: '#A98D68',
    bodyDark: '#6F5B43',
    bodyLight: '#D8BE98',
    pot: '#70594A',
    accent: '#604C3A',
  },
  {
    id: 'christmas',
    species: 'christmas',
    name: 'Grudnik',
    subtitle: 'Schlumbergera truncata',
    level: 50,
    price: 500,
    bonus: 2.3,
    body: '#3D9B58',
    bodyDark: '#226A3A',
    bodyLight: '#81CF91',
    pot: '#9A5C40',
    accent: '#F06A8A',
  },
];

const BIOMES = [
  {
    id: 'garden', name: 'Szklarnia', emoji: '🌿', requirement: 0, multiplier: 1,
    description: 'Stabilny biom. Większa szansa na esencję.', essenceBonus: 0.04,
  },
  {
    id: 'desert', name: 'Pustynia', emoji: '🏜️', requirement: 25000, multiplier: 1.6,
    description: 'Gorący biom wzmacniający kliknięcia.', clickBonus: 0.2,
  },
  {
    id: 'canyon', name: 'Kanion', emoji: '💎', requirement: 250000, multiplier: 2.5,
    description: 'Kryształowy biom zwiększający szansę na krytyk.', critBonus: 0.06,
  },
  {
    id: 'moon', name: 'Księżyc', emoji: '🌙', requirement: 3000000, multiplier: 4,
    description: 'Niska grawitacja wzmacnia automatyczną produkcję.', autoBonus: 0.35,
  },
  {
    id: 'nebula', name: 'Mgławica', emoji: '🌌', requirement: 50000000, multiplier: 7,
    description: 'Kosmiczny biom wzmacniający całe imperium.', globalBonus: 0.25,
  },
];

const UPGRADES = {
  click: {
    name: 'Grubsze pędy',
    description: '+2 punkty za każde kliknięcie',
    base: 20,
    growth: 1.52,
    unlock: 1,
    emoji: '🌱',
  },
  auto: {
    name: 'Automatyczne nawadnianie',
    description: '+2 punkty produkcji na sekundę',
    base: 90,
    growth: 1.68,
    unlock: 2,
    emoji: '💧',
  },
  fertilizer: {
    name: 'Lepsza ziemia',
    description: '+20% do kliknięć i produkcji automatycznej',
    base: 260,
    growth: 1.92,
    unlock: 3,
    emoji: '🪴',
  },
  critChance: {
    name: 'Selekcja zdrowych sadzonek',
    description: '+2,5% szansy na trafienie krytyczne',
    base: 480,
    growth: 1.86,
    unlock: 4,
    emoji: '🧬',
  },
  critPower: {
    name: 'Wyjątkowo dorodny okaz',
    description: '+0,5x do mnożnika trafienia krytycznego',
    base: 900,
    growth: 2.02,
    unlock: 5,
    emoji: '🏆',
  },
  combo: {
    name: 'Rytm pielęgnacji',
    description: 'Zwiększa premię za każde 10 punktów combo',
    base: 3200,
    growth: 2.14,
    unlock: 9,
    emoji: '⚡',
  },
  xp: {
    name: 'Notatnik botanika',
    description: '+15% zdobywanego doświadczenia',
    base: 8500,
    growth: 2.2,
    unlock: 12,
    emoji: '📗',
  },
  crystals: {
    name: 'Stoisko kolekcjonerskie',
    description: 'Dodatkowe kryształy przy każdym 5. poziomie',
    base: 20000,
    growth: 2.28,
    unlock: 15,
    emoji: '🏪',
  },
};

const RESEARCH = {
  click: {
    name: 'Kinetyka',
    description: '+10% kliknięcia',
    base: 1,
    max: 10,
  },
  auto: {
    name: 'Automatyzacja',
    description: '+12% produkcji pasywnej',
    base: 1,
    max: 10,
  },
  xp: {
    name: 'Botanika',
    description: '+10% zdobywanego XP',
    base: 2,
    max: 8,
  },
  luck: {
    name: 'Geologia',
    description: '+5% szansy na kryształ z awansu',
    base: 2,
    max: 8,
  },
};

const MILESTONES = [
  { id: 'click100', label: '100 kliknięć', type: 'clicks', target: 100, reward: 2 },
  { id: 'click1000', label: '1 000 kliknięć', type: 'clicks', target: 1000, reward: 4 },
  { id: 'click10000', label: '10 000 kliknięć', type: 'clicks', target: 10000, reward: 12 },
  { id: 'click100000', label: '100 000 kliknięć', type: 'clicks', target: 100000, reward: 40 },
  { id: 'points100k', label: '100 tys. punktów', type: 'lifetime', target: 100000, reward: 5 },
  { id: 'points10m', label: '10 mln punktów', type: 'lifetime', target: 10000000, reward: 15 },
  { id: 'points1b', label: '1 mld punktów', type: 'lifetime', target: 1000000000, reward: 50 },
  { id: 'level10', label: 'Poziom 10', type: 'level', target: 10, reward: 6 },
  { id: 'level25', label: 'Poziom 25', type: 'level', target: 25, reward: 18 },
  { id: 'level50', label: 'Poziom 50', type: 'level', target: 50, reward: 45 },
  { id: 'ascend1', label: 'Pierwsze odrodzenie', type: 'ascensions', target: 1, reward: 10 },
  { id: 'ascend5', label: '5 odrodzeń', type: 'ascensions', target: 5, reward: 35 },
  { id: 'skins5', label: 'Posiadaj 5 skinów', type: 'skins', target: 5, reward: 20 },
  { id: 'skins10', label: 'Zbierz wszystkie skiny', type: 'skins', target: 10, reward: 75 },
  { id: 'upgrade25', label: '25 poziomów ulepszeń', type: 'upgrades', target: 25, reward: 12 },
  { id: 'upgrade100', label: '100 poziomów ulepszeń', type: 'upgrades', target: 100, reward: 40 },
  { id: 'combo50', label: 'Combo 50', type: 'combo', target: 50, reward: 10 },
  { id: 'combo150', label: 'Combo 150', type: 'combo', target: 150, reward: 35 },
  { id: 'biome5', label: 'Łączny poziom biomów 5', type: 'biomes', target: 5, reward: 18 },
  { id: 'biome25', label: 'Łączny poziom biomów 25', type: 'biomes', target: 25, reward: 60 },
];

const EMPTY_NOTICE = {
  visible: false,
  type: 'info',
  title: '',
  message: '',
  confirmText: 'OK',
  cancelText: '',
  onConfirm: null,
};

export default function App() {
  const [points, setPoints] = useState(0);
  const [lifetimePoints, setLifetimePoints] = useState(0);
  const [totalClicks, setTotalClicks] = useState(0);
  const [level, setLevel] = useState(1);
  const [xp, setXp] = useState(0);
  const [crystals, setCrystals] = useState(0);
  const [seeds, setSeeds] = useState(0);
  const [ascensions, setAscensions] = useState(0);
  const [biomeEssence, setBiomeEssence] = useState(0);
  const [biomeLevels, setBiomeLevels] = useState(DEFAULT_BIOME_LEVELS);
  const [highestCombo, setHighestCombo] = useState(0);
  const [upgrades, setUpgrades] = useState(DEFAULT_UPGRADES);
  const [research, setResearch] = useState(DEFAULT_RESEARCH);
  const [ownedSkins, setOwnedSkins] = useState(['saguaro']);
  const [selectedSkinId, setSelectedSkinId] = useState('saguaro');
  const [selectedBiomeId, setSelectedBiomeId] = useState('garden');
  const [claimedMilestones, setClaimedMilestones] = useState([]);
  const [combo, setCombo] = useState(0);
  const [floating, setFloating] = useState([]);
  const [notice, setNotice] = useState(EMPTY_NOTICE);
  const [activeTab, setActiveTab] = useState('upgrades');
  const [loaded, setLoaded] = useState(false);

  const lastClickAt = useRef(0);
  const floatId = useRef(0);
  const resetLock = useRef(false);

  const skin = SKINS.find(item => item.id === selectedSkinId) || SKINS[0];
  const biome = BIOMES.find(item => item.id === selectedBiomeId) || BIOMES[0];

  const xpNeeded = getXpNeeded(level);
  const activeBiomeLevel = biomeLevels[biome.id] || 0;
  const biomeLevelMultiplier = 1 + activeBiomeLevel * 0.1;
  const effectiveBiomeMultiplier = biome.multiplier * biomeLevelMultiplier;
  const prestigeMultiplier = 1 + seeds * 0.12;
  const globalMultiplier =
    prestigeMultiplier *
    skin.bonus *
    effectiveBiomeMultiplier *
    (1 + upgrades.fertilizer * 0.2) *
    (1 + (biome.globalBonus || 0));

  const clickPower = Math.max(
    1,
    Math.floor(
      (1 + upgrades.click * 2) *
        globalMultiplier *
        (1 + (biome.clickBonus || 0)) *
        (1 + research.click * 0.1)
    )
  );

  const pointsPerSecond = Math.max(
    0,
    Math.floor(
      upgrades.auto *
        2 *
        globalMultiplier *
        (1 + (biome.autoBonus || 0)) *
        (1 + research.auto * 0.12)
    )
  );

  const critChance = Math.min(
    0.05 + upgrades.critChance * 0.025 + (biome.critBonus || 0),
    0.55
  );

  const critMultiplier = 2 + upgrades.critPower * 0.5;

  const xpMultiplier =
    (1 + upgrades.xp * 0.15) *
    (1 + research.xp * 0.1);

  const crystalChance = Math.min(
    0.08 + research.luck * 0.05,
    0.48
  );

  const ascensionReward = Math.max(
    0,
    Math.floor(Math.sqrt(lifetimePoints / 500000))
  );

  useEffect(() => {
    loadGame();
  }, []);

  useEffect(() => {
    if (!loaded) return;

    const interval = setInterval(saveGame, 1800);
    return () => clearInterval(interval);
  }, [
    loaded,
    points,
    lifetimePoints,
    totalClicks,
    level,
    xp,
    crystals,
    seeds,
    ascensions,
    biomeEssence,
    biomeLevels,
    highestCombo,
    upgrades,
    research,
    ownedSkins,
    selectedSkinId,
    selectedBiomeId,
    claimedMilestones,
  ]);

  useEffect(() => {
    if (!loaded || pointsPerSecond <= 0) return;

    const interval = setInterval(() => {
      grantPoints(pointsPerSecond);
    }, 1000);

    return () => clearInterval(interval);
  }, [loaded, pointsPerSecond]);

  useEffect(() => {
    if (combo <= 0) return;

    const timeout = setTimeout(() => {
      if (Date.now() - lastClickAt.current >= 1200) {
        setCombo(0);
      }
    }, 1250);

    return () => clearTimeout(timeout);
  }, [combo]);

  async function loadGame() {
    try {
      const raw = await AsyncStorage.getItem(SAVE_KEY);

      if (!raw) {
        setLoaded(true);
        return;
      }

      const data = JSON.parse(raw);

      setPoints(numberOr(data.points));
      setLifetimePoints(numberOr(data.lifetimePoints));
      setTotalClicks(numberOr(data.totalClicks));
      setLevel(Math.max(1, numberOr(data.level, 1)));
      setXp(numberOr(data.xp));
      setCrystals(numberOr(data.crystals));
      setSeeds(numberOr(data.seeds));
      setAscensions(numberOr(data.ascensions));
      setBiomeEssence(numberOr(data.biomeEssence));
      setBiomeLevels({ ...DEFAULT_BIOME_LEVELS, ...(data.biomeLevels || {}) });
      setHighestCombo(numberOr(data.highestCombo));
      setUpgrades({ ...DEFAULT_UPGRADES, ...(data.upgrades || {}) });
      setResearch({ ...DEFAULT_RESEARCH, ...(data.research || {}) });
      setOwnedSkins(
        Array.isArray(data.ownedSkins) && data.ownedSkins.length
          ? data.ownedSkins
          : ['saguaro']
      );
      setSelectedSkinId(data.selectedSkinId || 'saguaro');
      setSelectedBiomeId(data.selectedBiomeId || 'garden');
      setClaimedMilestones(
        Array.isArray(data.claimedMilestones)
          ? data.claimedMilestones
          : []
      );
    } catch (error) {
      console.log('Błąd wczytywania:', error);
    } finally {
      setLoaded(true);
    }
  }

  async function saveGame() {
    if (resetLock.current) return;

    try {
      await AsyncStorage.setItem(
        SAVE_KEY,
        JSON.stringify({
          points,
          lifetimePoints,
          totalClicks,
          level,
          xp,
          crystals,
          seeds,
          ascensions,
          biomeEssence,
          biomeLevels,
          highestCombo,
          upgrades,
          research,
          ownedSkins,
          selectedSkinId,
          selectedBiomeId,
          claimedMilestones,
        })
      );
    } catch (error) {
      console.log('Błąd zapisu:', error);
    }
  }

  function grantPoints(amount) {
    const value = Math.max(0, Math.floor(amount));
    setPoints(current => current + value);
    setLifetimePoints(current => current + value);
  }

  function clickCactus() {
    const now = Date.now();
    const nextCombo =
      now - lastClickAt.current < 950
        ? Math.min(combo + 1, 150)
        : 1;

    lastClickAt.current = now;
    setCombo(nextCombo);
    setHighestCombo(current => Math.max(current, nextCombo));

    const comboSteps = Math.floor(nextCombo / 10);
    const comboMultiplier =
      1 + comboSteps * (0.12 + upgrades.combo * 0.08);

    const golden = Math.random() < 0.012 + seeds * 0.001;
    const critical = !golden && Math.random() < critChance;

    let earned = clickPower * comboMultiplier;
    let kind = 'normal';

    if (critical) {
      earned *= critMultiplier;
      kind = 'critical';
    }

    if (golden) {
      earned *= 12;
      kind = 'golden';
    }

    earned = Math.max(1, Math.floor(earned));

    grantPoints(earned);
    setTotalClicks(current => current + 1);
    addXp(
      Math.max(
        1,
        Math.floor((golden ? 6 : critical ? 3 : 1) * xpMultiplier)
      )
    );
    const essenceChance = 0.08 + (biome.essenceBonus || 0);
    if (golden || Math.random() < essenceChance) {
      setBiomeEssence(current => current + (golden ? 3 : 1));
    }

    addFloating(earned, kind);
  }

  function addFloating(value, kind) {
    floatId.current += 1;
    const id = floatId.current;

    const item = {
      id,
      value,
      kind,
      left: 3 + Math.random() * 82,
      top: 2 + Math.random() * 70,
      rotation: -14 + Math.random() * 28,
      scale: 0.85 + Math.random() * 0.4,
    };

    setFloating(current => [...current.slice(-12), item]);

    setTimeout(() => {
      setFloating(current => current.filter(item => item.id !== id));
    }, 720);
  }

  function addXp(amount) {
    let nextXp = xp + amount;
    let nextLevel = level;
    let levelsGained = 0;
    let crystalGain = 0;

    while (nextXp >= getXpNeeded(nextLevel)) {
      nextXp -= getXpNeeded(nextLevel);
      nextLevel += 1;
      levelsGained += 1;

      if (Math.random() < crystalChance) {
        crystalGain += 1;
      }

      if (upgrades.crystals > 0 && nextLevel % 5 === 0) {
        crystalGain += upgrades.crystals;
      }
    }

    setXp(nextXp);

    if (levelsGained > 0) {
      setLevel(nextLevel);

      const reward = nextLevel * 30 * levelsGained;
      grantPoints(reward);

      if (crystalGain > 0) {
        setCrystals(current => current + crystalGain);
      }
    }
  }

  function upgradePrice(type) {
    const item = UPGRADES[type];

    return Math.floor(
      item.base * Math.pow(item.growth, upgrades[type])
    );
  }

  function buyUpgrade(type) {
    const item = UPGRADES[type];

    if (level < item.unlock) {
      showNotice({
        type: 'locked',
        title: 'Ulepszenie zablokowane',
        message: `Odblokuje się na poziomie ${item.unlock}.`,
        confirmText: 'Rozumiem',
      });
      return;
    }

    const price = upgradePrice(type);

    if (points < price) {
      showNotice({
        type: 'error',
        title: 'Za mało punktów',
        message: `Brakuje ${formatNumber(price - points)} punktów.`,
        confirmText: 'Wracam',
      });
      return;
    }

    setPoints(current => current - price);
    setUpgrades(current => ({
      ...current,
      [type]: current[type] + 1,
    }));
  }

  function researchCost(type) {
    return RESEARCH[type].base + research[type];
  }

  function buyResearch(type) {
    const item = RESEARCH[type];
    const currentLevel = research[type];
    const cost = researchCost(type);

    if (currentLevel >= item.max) return;

    if (seeds < cost) {
      showNotice({
        type: 'error',
        title: 'Za mało nasion',
        message: `Potrzebujesz ${cost} nasion odrodzenia.`,
        confirmText: 'Rozumiem',
      });
      return;
    }

    setSeeds(current => current - cost);
    setResearch(current => ({
      ...current,
      [type]: current[type] + 1,
    }));
  }

  function chooseSkin(item) {
    const owned = ownedSkins.includes(item.id);

    if (owned) {
      setSelectedSkinId(item.id);
      return;
    }

    if (level < item.level) {
      showNotice({
        type: 'locked',
        title: 'Skin zablokowany',
        message: `Osiągnij poziom ${item.level}.`,
        confirmText: 'Rozumiem',
      });
      return;
    }

    if (crystals < item.price) {
      showNotice({
        type: 'error',
        title: 'Za mało kryształów',
        message: `Brakuje ${item.price - crystals} kryształów.`,
        confirmText: 'Wracam',
      });
      return;
    }

    setCrystals(current => current - item.price);
    setOwnedSkins(current => [...current, item.id]);
    setSelectedSkinId(item.id);
  }

  function chooseBiome(item) {
    if (lifetimePoints < item.requirement) {
      showNotice({
        type: 'locked',
        title: 'Biom zablokowany',
        message: `Zdobądź łącznie ${formatNumber(
          item.requirement
        )} punktów.`,
        confirmText: 'Rozumiem',
      });
      return;
    }

    setSelectedBiomeId(item.id);
  }

  function biomeUpgradeCost(item) {
    const currentLevel = biomeLevels[item.id] || 0;
    return Math.floor(10 * Math.pow(currentLevel + 1, 2));
  }

  function upgradeActiveBiome() {
    const currentLevel = biomeLevels[biome.id] || 0;

    if (currentLevel >= 10) {
      showNotice({
        type: 'success',
        title: 'Biom maksymalny',
        message: 'Ten biom osiągnął poziom 10.',
        confirmText: 'Świetnie',
      });
      return;
    }

    const cost = biomeUpgradeCost(biome);

    if (biomeEssence < cost) {
      showNotice({
        type: 'error',
        title: 'Za mało esencji',
        message: `Potrzebujesz ${cost} esencji biomu.`,
        confirmText: 'Gram dalej',
      });
      return;
    }

    const nextLevel = currentLevel + 1;
    setBiomeEssence(current => current - cost);
    setBiomeLevels(current => ({
      ...current,
      [biome.id]: nextLevel,
    }));

    if (nextLevel === 5 || nextLevel === 10) {
      const reward = nextLevel === 5 ? 5 : 15;
      setCrystals(current => current + reward);
      showNotice({
        type: 'success',
        title: `Mistrzostwo: ${biome.name}`,
        message: `Biom osiągnął poziom ${nextLevel}. Otrzymujesz ${reward} kryształów.`,
        confirmText: 'Odbierz',
      });
    }
  }

  function milestoneValue(item) {
    if (item.type === 'clicks') return totalClicks;
    if (item.type === 'lifetime') return lifetimePoints;
    if (item.type === 'level') return level;
    if (item.type === 'ascensions') return ascensions;
    if (item.type === 'skins') return ownedSkins.length;
    if (item.type === 'upgrades') return Object.values(upgrades).reduce((sum, value) => sum + value, 0);
    if (item.type === 'combo') return highestCombo;
    if (item.type === 'biomes') return Object.values(biomeLevels).reduce((sum, value) => sum + value, 0);
    return 0;
  }

  function claimMilestone(item) {
    if (claimedMilestones.includes(item.id)) return;

    const value = milestoneValue(item);

    if (value < item.target) {
      showNotice({
        type: 'info',
        title: 'Cel jeszcze nieukończony',
        message: `${formatNumber(value)} / ${formatNumber(item.target)}`,
        confirmText: 'Gram dalej',
      });
      return;
    }

    setClaimedMilestones(current => [...current, item.id]);
    setCrystals(current => current + item.reward);
  }

  function ascend() {
    if (ascensionReward < 1) {
      showNotice({
        type: 'locked',
        title: 'Odrodzenie zablokowane',
        message: 'Zdobądź co najmniej 500 tys. punktów łącznie.',
        confirmText: 'Rozumiem',
      });
      return;
    }

    showNotice({
      type: 'warning',
      title: 'Odrodzenie plantacji',
      message:
        `Zresetujesz punkty, poziom i zwykłe ulepszenia. ` +
        `Zachowasz badania, skiny, kryształy i statystyki. ` +
        `Otrzymasz ${ascensionReward} nasion. Każde daje +12% produkcji.`,
      confirmText: 'Odrodź',
      cancelText: 'Anuluj',
      onConfirm: () => {
        setPoints(0);
        setLevel(1);
        setXp(0);
        setUpgrades({ ...DEFAULT_UPGRADES });
        setCombo(0);
        setFloating([]);
        setSeeds(current => current + ascensionReward);
        setAscensions(current => current + 1);
        setSelectedBiomeId('garden');
      },
    });
  }

  function resetGame() {
    showNotice({
      type: 'danger',
      title: 'Pełny reset',
      message:
        'Zostaną usunięte punkty, kliknięcia, statystyki, skiny, badania, kryształy, nasiona i odrodzenia.',
      confirmText: 'Usuń wszystko',
      cancelText: 'Anuluj',
      onConfirm: async () => {
        resetLock.current = true;

        setPoints(0);
        setLifetimePoints(0);
        setTotalClicks(0);
        setLevel(1);
        setXp(0);
        setCrystals(0);
        setSeeds(0);
        setAscensions(0);
        setBiomeEssence(0);
        setBiomeLevels({ ...DEFAULT_BIOME_LEVELS });
        setHighestCombo(0);
        setUpgrades({ ...DEFAULT_UPGRADES });
        setResearch({ ...DEFAULT_RESEARCH });
        setOwnedSkins(['saguaro']);
        setSelectedSkinId('saguaro');
        setSelectedBiomeId('garden');
        setClaimedMilestones([]);
        setCombo(0);
        setFloating([]);
        lastClickAt.current = 0;

        await AsyncStorage.removeItem(SAVE_KEY);

        setTimeout(() => {
          resetLock.current = false;
        }, 600);
      },
    });
  }

  function showNotice(config) {
    setNotice({
      ...EMPTY_NOTICE,
      ...config,
      visible: true,
    });
  }

  function closeNotice() {
    setNotice(current => ({
      ...current,
      visible: false,
    }));
  }

  function confirmNotice() {
    const action = notice.onConfirm;
    closeNotice();

    if (action) {
      setTimeout(action, 120);
    }
  }

  const nextBiome = BIOMES.find(
    item => lifetimePoints < item.requirement
  );

  if (!loaded) {
    return (
      <SafeAreaView style={styles.loading}>
        <StatusBar barStyle="light-content" />
        <Cactus skin={SKINS[0]} size={0.72} />
        <Text style={styles.loadingText}>Ładowanie plantacji...</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />

      <Notice
        notice={notice}
        onClose={closeNotice}
        onConfirm={confirmNotice}
      />

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <View>
            <Text style={styles.title}>Cactus Clicker</Text>
            <Text style={styles.subtitle}>{biome.name}</Text>
          </View>

          <Pressable onPress={resetGame} style={styles.resetButton}>
            <Text style={styles.resetButtonText}>RESET</Text>
          </Pressable>
        </View>

        <View style={styles.currencyRow}>
          <Currency label="Kryształy" value={crystals} color="#67D4E3" />
          <Currency label="Nasiona" value={seeds} color="#D2AD69" />
          <Currency label="Odrodzenia" value={ascensions} color="#B397EA" />
          <Currency label="Esencja" value={biomeEssence} color="#E7C45F" />
        </View>

        <View style={styles.levelCard}>
          <View style={styles.levelTop}>
            <Text style={styles.levelTitle}>Poziom {level}</Text>
            <Text style={styles.levelXp}>
              {formatNumber(xp)} / {formatNumber(xpNeeded)} XP
            </Text>
          </View>
          <Progress value={xp / xpNeeded} />
        </View>

        <View style={styles.scoreCard}>
          <Text style={styles.scoreLabel}>Punkty plantacji</Text>
          <Text
            style={styles.score}
            numberOfLines={1}
            adjustsFontSizeToFit
          >
            {formatNumber(points)}
          </Text>

          <View style={styles.statsRow}>
            <Stat label="za klik" value={formatNumber(clickPower)} />
            <View style={styles.divider} />
            <Stat label="na sekundę" value={formatNumber(pointsPerSecond)} />
            <View style={styles.divider} />
            <Stat
              label="mnożnik"
              value={`${shortDecimal(globalMultiplier)}x`}
            />
          </View>
        </View>

        <View style={styles.cactusZone}>
          <View
            pointerEvents="none"
            style={styles.floatingLayer}
          >
            {floating.map(item => (
              <Text
                key={item.id}
                pointerEvents="none"
                selectable={false}
                style={[
                  styles.floatText,
                  item.kind === 'critical' && styles.floatCritical,
                  item.kind === 'golden' && styles.floatGolden,
                  {
                    left: `${item.left}%`,
                    top: `${item.top}%`,
                    transform: [
                      { rotate: `${item.rotation}deg` },
                      { scale: item.scale },
                    ],
                  },
                ]}
              >
                {item.kind === 'critical'
                  ? `CRIT +${formatNumber(item.value)}`
                  : item.kind === 'golden'
                  ? `GOLD +${formatNumber(item.value)}`
                  : `+${formatNumber(item.value)}`}
              </Text>
            ))}
          </View>

          <Pressable
            onPress={clickCactus}
            style={({ pressed }) => [
              styles.cactusButton,
              pressed && styles.cactusPressed,
            ]}
          >
            <Cactus skin={skin} size={1} />
          </Pressable>

          <Text style={styles.tapText}>Kliknij kaktusa</Text>

          {combo > 1 && (
            <View style={styles.comboBox}>
              <Text style={styles.comboTitle}>COMBO {combo}</Text>
              <Text style={styles.comboText}>
                bonus{' '}
                {Math.round(
                  Math.floor(combo / 10) *
                    (0.12 + upgrades.combo * 0.08) *
                    100
                )}
                %
              </Text>
            </View>
          )}
        </View>

        <View style={styles.worldCard}>
          <View style={styles.sectionHeader}>
            <View>
              <Text style={styles.sectionTitle}>Podróż przez światy</Text>
              <Text style={styles.sectionDescription}>
                {biome.description}
              </Text>
            </View>
            <Text style={styles.worldBonus}>
              {shortDecimal(effectiveBiomeMultiplier)}x
            </Text>
          </View>

          <View style={styles.biomeMasteryCard}>
            <View style={styles.biomeMasteryTop}>
              <View>
                <Text style={styles.biomeMasteryTitle}>
                  Mistrzostwo biomu: {activeBiomeLevel}/10
                </Text>
                <Text style={styles.biomeMasteryText}>
                  Każdy poziom dodaje +10% do mnożnika biomu.
                </Text>
              </View>
              <Pressable
                onPress={upgradeActiveBiome}
                style={[
                  styles.biomeUpgradeButton,
                  biomeEssence >= biomeUpgradeCost(biome) &&
                    activeBiomeLevel < 10 &&
                    styles.biomeUpgradeButtonReady,
                ]}
              >
                <Text style={styles.biomeUpgradeButtonText}>
                  {activeBiomeLevel >= 10
                    ? 'MAX'
                    : `${biomeUpgradeCost(biome)} ✨`}
                </Text>
              </Pressable>
            </View>
            <Progress value={activeBiomeLevel / 10} gold />
          </View>

          {nextBiome ? (
            <>
              <Text style={styles.nextBiome}>
                Następny: {nextBiome.name}
              </Text>
              <Progress
                value={lifetimePoints / nextBiome.requirement}
                gold
              />
              <Text style={styles.progressCaption}>
                {formatNumber(lifetimePoints)} /{' '}
                {formatNumber(nextBiome.requirement)}
              </Text>
            </>
          ) : (
            <Text style={styles.completeText}>
              Wszystkie biomy odblokowane
            </Text>
          )}

          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.horizontalList}
          >
            {BIOMES.map(item => {
              const unlocked =
                lifetimePoints >= item.requirement;
              const selected = item.id === selectedBiomeId;

              return (
                <Pressable
                  key={item.id}
                  onPress={() => chooseBiome(item)}
                  style={[
                    styles.biomeCard,
                    selected && styles.biomeSelected,
                    !unlocked && styles.locked,
                  ]}
                >
                  <Text style={styles.biomeEmoji}>{item.emoji}</Text>
                  <Text style={styles.biomeName}>{item.name}</Text>
                  <Text style={styles.biomeValue}>
                    {unlocked
                      ? `${shortDecimal(item.multiplier * (1 + (biomeLevels[item.id] || 0) * 0.1))}x · P${biomeLevels[item.id] || 0}`
                      : formatNumber(item.requirement)}
                  </Text>
                </Pressable>
              );
            })}
          </ScrollView>
        </View>

        <View style={styles.tabs}>
          {[
            ['upgrades', 'Ulepszenia'],
            ['research', 'Badania'],
            ['skins', 'Skiny'],
            ['goals', 'Cele'],
          ].map(([id, label]) => (
            <Pressable
              key={id}
              onPress={() => setActiveTab(id)}
              style={[
                styles.tab,
                activeTab === id && styles.tabActive,
              ]}
            >
              <Text
                style={[
                  styles.tabText,
                  activeTab === id && styles.tabTextActive,
                ]}
              >
                {label}
              </Text>
            </Pressable>
          ))}
        </View>

        {activeTab === 'upgrades' && (
          <View style={styles.list}>
            {Object.entries(UPGRADES).map(([type, item]) => {
              const price = upgradePrice(type);
              const unlocked = level >= item.unlock;
              const affordable = points >= price;

              return (
                <View
                  key={type}
                  style={[
                    styles.rowCard,
                    !unlocked && styles.locked,
                  ]}
                >
                  <View style={styles.emojiIcon}>
                    <Text style={styles.emojiIconText}>
                      {item.emoji}
                    </Text>
                  </View>

                  <View style={styles.flex}>
                    <Text style={styles.rowTitle}>{item.name}</Text>
                    <Text style={styles.rowDescription}>
                      {unlocked
                        ? item.description
                        : `Odblokowanie: poziom ${item.unlock}`}
                    </Text>
                    <Text style={styles.rowLevel}>
                      Poziom {upgrades[type]}
                    </Text>
                  </View>

                  <Pressable
                    onPress={() => buyUpgrade(type)}
                    style={[
                      styles.buyButton,
                      unlocked &&
                        affordable &&
                        styles.buyButtonReady,
                    ]}
                  >
                    <Text
                      style={[
                        styles.buyButtonText,
                        unlocked &&
                          affordable &&
                          styles.buyButtonTextReady,
                      ]}
                    >
                      {formatNumber(price)}
                    </Text>
                  </Pressable>
                </View>
              );
            })}
          </View>
        )}

        {activeTab === 'research' && (
          <View style={styles.list}>
            <View style={styles.researchInfo}>
              <Text style={styles.researchInfoTitle}>
                Stały rozwój
              </Text>
              <Text style={styles.researchInfoText}>
                Badania i skiny nie resetują się po odrodzeniu.
              </Text>
            </View>

            {Object.entries(RESEARCH).map(([type, item]) => {
              const current = research[type];
              const maxed = current >= item.max;
              const cost = researchCost(type);

              return (
                <View key={type} style={styles.rowCard}>
                  <View style={styles.researchIcon}>
                    <Text style={styles.researchIconText}>B</Text>
                  </View>

                  <View style={styles.flex}>
                    <Text style={styles.rowTitle}>{item.name}</Text>
                    <Text style={styles.rowDescription}>
                      {item.description}
                    </Text>
                    <Text style={styles.rowLevel}>
                      Poziom {current}/{item.max}
                    </Text>
                  </View>

                  <Pressable
                    disabled={maxed}
                    onPress={() => buyResearch(type)}
                    style={[
                      styles.seedButton,
                      seeds >= cost &&
                        !maxed &&
                        styles.seedButtonReady,
                    ]}
                  >
                    <Text style={styles.seedButtonText}>
                      {maxed ? 'MAX' : `${cost} N`}
                    </Text>
                  </Pressable>
                </View>
              );
            })}

            <Pressable
              onPress={ascend}
              style={[
                styles.ascendCard,
                ascensionReward < 1 && styles.locked,
              ]}
            >
              <View style={styles.ascendIcon}>
                <Text style={styles.ascendIconText}>O</Text>
              </View>
              <View style={styles.flex}>
                <Text style={styles.ascendTitle}>
                  Odrodzenie plantacji
                </Text>
                <Text style={styles.ascendText}>
                  Nagroda teraz: {ascensionReward} nasion
                </Text>
              </View>
              <Text style={styles.arrow}>›</Text>
            </Pressable>
          </View>
        )}

        {activeTab === 'skins' && (
          <View style={styles.skinGrid}>
            {SKINS.map(item => {
              const owned = ownedSkins.includes(item.id);
              const selected = item.id === selectedSkinId;
              const unlocked = level >= item.level;

              return (
                <Pressable
                  key={item.id}
                  onPress={() => chooseSkin(item)}
                  style={[
                    styles.skinCard,
                    selected && styles.skinSelected,
                    !unlocked && styles.locked,
                  ]}
                >
                  <Cactus skin={item} size={0.52} />
                  <Text style={styles.skinName}>{item.name}</Text>
                  <Text style={styles.skinSpecies}>{item.subtitle}</Text>
                  <Text style={styles.skinBonus}>
                    bonus {shortDecimal(item.bonus)}x
                  </Text>
                  <View style={styles.skinAction}>
                    <Text style={styles.skinActionText}>
                      {selected
                        ? 'Wybrany'
                        : owned
                        ? 'Wybierz'
                        : unlocked
                        ? `${item.price} kryształów`
                        : `Poziom ${item.level}`}
                    </Text>
                  </View>
                </Pressable>
              );
            })}
          </View>
        )}

        {activeTab === 'goals' && (
          <View style={styles.list}>
            {MILESTONES.map(item => {
              const value = milestoneValue(item);
              const claimed =
                claimedMilestones.includes(item.id);
              const ready = value >= item.target;

              return (
                <Pressable
                  key={item.id}
                  onPress={() => claimMilestone(item)}
                  style={[
                    styles.goalCard,
                    ready &&
                      !claimed &&
                      styles.goalCardReady,
                  ]}
                >
                  <View
                    style={[
                      styles.goalIcon,
                      claimed && styles.goalIconDone,
                    ]}
                  >
                    <Text
                      style={[
                        styles.goalIconText,
                        claimed && styles.goalIconTextDone,
                      ]}
                    >
                      {claimed ? '✓' : '•'}
                    </Text>
                  </View>

                  <View style={styles.flex}>
                    <Text style={styles.goalTitle}>{item.label}</Text>
                    <Progress
                      value={value / item.target}
                      muted={claimed}
                    />
                    <Text style={styles.goalProgress}>
                      {formatNumber(
                        Math.min(value, item.target)
                      )}{' '}
                      / {formatNumber(item.target)}
                    </Text>
                  </View>

                  <View style={styles.goalReward}>
                    <Text style={styles.goalRewardSymbol}>◆</Text>
                    <Text style={styles.goalRewardText}>
                      {claimed ? '✓' : item.reward}
                    </Text>
                  </View>
                </Pressable>
              );
            })}

            <View style={styles.statisticsCard}>
              <Text style={styles.sectionTitle}>
                Statystyki kariery
              </Text>
              <Statistic
                label="Wszystkie kliknięcia"
                value={formatNumber(totalClicks)}
              />
              <Statistic
                label="Punkty łącznie"
                value={formatNumber(lifetimePoints)}
              />
              <Statistic
                label="Aktualny poziom"
                value={formatNumber(level)}
              />
              <Statistic
                label="Odrodzenia"
                value={formatNumber(ascensions)}
              />
              <Statistic
                label="Najwyższe combo"
                value={formatNumber(highestCombo)}
              />
              <Statistic
                label="Poziomy biomów"
                value={formatNumber(Object.values(biomeLevels).reduce((sum, value) => sum + value, 0))}
              />
              <Statistic
                label="Posiadane skiny"
                value={`${ownedSkins.length}/${SKINS.length}`}
              />
            </View>
          </View>
        )}

        <Text style={styles.footer}>
          Postęp zapisuje się automatycznie
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
}

function Cactus({ skin, size }) {
  const scale = size || 1;
  const species = skin.species || 'saguaro';

  return (
    <View
      pointerEvents="none"
      style={[
        styles.cactusCanvas,
        {
          width: 190 * scale,
          height: 205 * scale,
        },
      ]}
    >
      <PlantPot skin={skin} scale={scale} />

      {species === 'saguaro' && <SaguaroPlant skin={skin} scale={scale} />}
      {species === 'barrel' && <BarrelPlant skin={skin} scale={scale} />}
      {species === 'bunny' && <BunnyPlant skin={skin} scale={scale} />}
      {species === 'moon' && <MoonPlant skin={skin} scale={scale} />}
      {species === 'oldman' && <OldManPlant skin={skin} scale={scale} />}
      {species === 'aloe' && <AloePlant skin={skin} scale={scale} />}
      {species === 'haworthia' && <HaworthiaPlant skin={skin} scale={scale} />}
      {species === 'echeveria' && <EcheveriaPlant skin={skin} scale={scale} />}
      {species === 'lithops' && <LithopsPlant skin={skin} scale={scale} />}
      {species === 'christmas' && <ChristmasPlant skin={skin} scale={scale} />}
    </View>
  );
}

function PlantPot({ skin, scale }) {
  return (
    <>
      <View
        style={[
          styles.cactusShadow,
          {
            width: 118 * scale,
            height: 16 * scale,
            borderRadius: 10 * scale,
            left: 36 * scale,
            bottom: 0,
          },
        ]}
      />
      <View
        style={[
          styles.potTop,
          {
            width: 100 * scale,
            height: 22 * scale,
            borderRadius: 9 * scale,
            left: 45 * scale,
            bottom: 29 * scale,
            backgroundColor: skin.pot,
          },
        ]}
      />
      <View
        style={[
          styles.potBody,
          {
            width: 82 * scale,
            height: 48 * scale,
            left: 54 * scale,
            bottom: 0,
            backgroundColor: skin.pot,
            borderBottomLeftRadius: 20 * scale,
            borderBottomRightRadius: 20 * scale,
          },
        ]}
      />
    </>
  );
}

function PlantPiece({ style }) {
  return <View style={[styles.plantPiece, style]} />;
}

function SaguaroPlant({ skin, scale }) {
  return (
    <>
      <PlantPiece style={{
        width: 55 * scale, height: 135 * scale, borderRadius: 28 * scale,
        left: 68 * scale, bottom: 44 * scale, backgroundColor: skin.body,
        borderColor: skin.bodyDark, borderWidth: 4 * scale,
      }} />
      <PlantPiece style={{
        width: 34 * scale, height: 72 * scale, borderRadius: 18 * scale,
        left: 38 * scale, bottom: 78 * scale, backgroundColor: skin.body,
        borderColor: skin.bodyDark, borderWidth: 4 * scale,
      }} />
      <PlantPiece style={{
        width: 46 * scale, height: 30 * scale, borderRadius: 16 * scale,
        left: 38 * scale, bottom: 78 * scale, backgroundColor: skin.body,
        borderColor: skin.bodyDark, borderWidth: 4 * scale,
      }} />
      <PlantPiece style={{
        width: 34 * scale, height: 86 * scale, borderRadius: 18 * scale,
        right: 34 * scale, bottom: 92 * scale, backgroundColor: skin.body,
        borderColor: skin.bodyDark, borderWidth: 4 * scale,
      }} />
      <PlantPiece style={{
        width: 48 * scale, height: 31 * scale, borderRadius: 16 * scale,
        right: 34 * scale, bottom: 92 * scale, backgroundColor: skin.body,
        borderColor: skin.bodyDark, borderWidth: 4 * scale,
      }} />
      <Spikes skin={skin} scale={scale} points={[
        [81,45],[104,53],[82,79],[104,88],[83,116],
        [104,126],[50,83],[51,115],[139,72],[140,108],
      ]} />
    </>
  );
}

function BarrelPlant({ skin, scale }) {
  return (
    <>
      <PlantPiece style={{
        width: 116 * scale, height: 116 * scale, borderRadius: 58 * scale,
        left: 37 * scale, bottom: 43 * scale, backgroundColor: skin.body,
        borderColor: skin.bodyDark, borderWidth: 5 * scale,
      }} />
      {[0,1,2,3,4].map(index => (
        <View key={index} style={{
          position: 'absolute', zIndex: 7, width: 4 * scale,
          height: 91 * scale, borderRadius: 3 * scale,
          left: (57 + index * 19) * scale, bottom: 55 * scale,
          backgroundColor: skin.bodyLight, opacity: 0.45,
        }} />
      ))}
      <Spikes skin={skin} scale={scale} points={[
        [53,73],[78,59],[105,58],[132,73],[49,105],
        [76,99],[106,96],[137,106],[62,135],[95,139],[126,133],
      ]} />
    </>
  );
}

function BunnyPlant({ skin, scale }) {
  const pads = [
    [64,78,64,86,-8],[101,57,58,94,7],[42,48,48,68,-15],[125,43,46,66,14],
  ];
  return (
    <>
      {pads.map(([left,bottom,width,height,rotation], index) => (
        <PlantPiece key={index} style={{
          width: width * scale, height: height * scale,
          borderRadius: (width / 2) * scale, left: left * scale,
          bottom: bottom * scale, backgroundColor: skin.body,
          borderColor: skin.bodyDark, borderWidth: 4 * scale,
          transform: [{ rotate: `${rotation}deg` }],
        }} />
      ))}
      <Spikes skin={skin} scale={scale} points={[
        [63,74],[80,91],[103,67],[123,85],[54,125],[78,136],
        [112,120],[137,130],[56,53],[136,55],
      ]} />
    </>
  );
}

function MoonPlant({ skin, scale }) {
  return (
    <>
      <PlantPiece style={{
        width: 38 * scale, height: 92 * scale, borderRadius: 19 * scale,
        left: 76 * scale, bottom: 43 * scale, backgroundColor: skin.body,
        borderColor: skin.bodyDark, borderWidth: 4 * scale,
      }} />
      <PlantPiece style={{
        width: 91 * scale, height: 68 * scale, borderRadius: 34 * scale,
        left: 50 * scale, bottom: 118 * scale, backgroundColor: skin.accent,
        borderColor: '#9E3436', borderWidth: 4 * scale,
      }} />
      {[0,1,2,3,4].map(index => (
        <View key={index} style={{
          position: 'absolute', zIndex: 8, width: 7 * scale,
          height: 44 * scale, borderRadius: 5 * scale,
          left: (68 + index * 14) * scale, bottom: 130 * scale,
          backgroundColor: '#FF9690', opacity: 0.7,
          transform: [{ rotate: `${(index - 2) * 8}deg` }],
        }} />
      ))}
    </>
  );
}

function OldManPlant({ skin, scale }) {
  return (
    <>
      <PlantPiece style={{
        width: 76 * scale, height: 142 * scale, borderRadius: 38 * scale,
        left: 57 * scale, bottom: 42 * scale, backgroundColor: skin.body,
        borderColor: skin.bodyDark, borderWidth: 4 * scale,
      }} />
      {Array.from({ length: 13 }).map((_, index) => (
        <View key={index} style={{
          position: 'absolute', zIndex: 9, width: 3 * scale,
          height: (100 + (index % 3) * 15) * scale,
          borderRadius: 3 * scale, left: (62 + index * 5.2) * scale,
          bottom: (48 + (index % 2) * 4) * scale,
          backgroundColor: skin.accent, opacity: 0.72,
          transform: [{ rotate: `${-8 + (index % 5) * 4}deg` }],
        }} />
      ))}
    </>
  );
}

function AloePlant({ skin, scale }) {
  const leaves = [
    [83,40,23,129,-3],[57,39,22,110,-22],[108,40,22,112,22],
    [39,40,20,86,-38],[129,40,20,88,38],[72,40,20,88,-12],[99,40,20,92,12],
  ];
  return (
    <>
      {leaves.map(([left,bottom,width,height,rotation], index) => (
        <PlantPiece key={index} style={{
          width: width * scale, height: height * scale,
          borderTopLeftRadius: 18 * scale, borderTopRightRadius: 18 * scale,
          borderBottomLeftRadius: 8 * scale, borderBottomRightRadius: 8 * scale,
          left: left * scale, bottom: bottom * scale,
          backgroundColor: index % 2 ? skin.bodyDark : skin.body,
          borderColor: skin.bodyDark, borderWidth: 2 * scale,
          transform: [{ rotate: `${rotation}deg` }],
        }} />
      ))}
    </>
  );
}

function HaworthiaPlant({ skin, scale }) {
  const leaves = [
    [84,42,22,105,0],[60,42,22,91,-25],[107,42,22,92,25],
    [42,42,20,72,-43],[128,42,20,74,43],[72,42,19,72,-12],[99,42,19,74,12],
  ];
  return (
    <>
      {leaves.map(([left,bottom,width,height,rotation], index) => (
        <View key={index} style={{
          position: 'absolute', zIndex: 5 + index,
          width: width * scale, height: height * scale,
          borderTopLeftRadius: 15 * scale, borderTopRightRadius: 15 * scale,
          borderBottomLeftRadius: 7 * scale, borderBottomRightRadius: 7 * scale,
          left: left * scale, bottom: bottom * scale,
          backgroundColor: skin.body, borderColor: skin.bodyDark,
          borderWidth: 3 * scale, transform: [{ rotate: `${rotation}deg` }],
          overflow: 'hidden',
        }}>
          {[18,37,56].map((top, stripeIndex) => (
            <View key={stripeIndex} style={{
              position: 'absolute', width: '100%', height: 4 * scale,
              top: top * scale, backgroundColor: skin.accent, opacity: 0.8,
            }} />
          ))}
        </View>
      ))}
    </>
  );
}

function EcheveriaPlant({ skin, scale }) {
  const rings = [
    { count: 10, radius: 50, width: 36, height: 72, bottom: 44 },
    { count: 8, radius: 34, width: 31, height: 61, bottom: 55 },
    { count: 6, radius: 20, width: 26, height: 48, bottom: 68 },
  ];
  return (
    <>
      {rings.flatMap((ring, ringIndex) =>
        Array.from({ length: ring.count }).map((_, index) => {
          const angle = (360 / ring.count) * index;
          const radians = angle * Math.PI / 180;
          const left = 95 + Math.cos(radians) * ring.radius - ring.width / 2;
          const bottom = ring.bottom + Math.sin(radians) * ring.radius * 0.35;
          return (
            <PlantPiece key={`${ringIndex}-${index}`} style={{
              width: ring.width * scale, height: ring.height * scale,
              borderTopLeftRadius: 20 * scale, borderTopRightRadius: 20 * scale,
              borderBottomLeftRadius: 12 * scale, borderBottomRightRadius: 12 * scale,
              left: left * scale, bottom: bottom * scale,
              backgroundColor: ringIndex === 0 ? skin.bodyDark : skin.body,
              borderColor: skin.bodyLight, borderWidth: 2 * scale,
              transform: [{ rotate: `${angle + 90}deg` }],
            }} />
          );
        })
      )}
    </>
  );
}

function LithopsPlant({ skin, scale }) {
  const stones = [
    [48,47,47,61,-8],[82,44,49,67,5],[118,48,39,57,10],
  ];
  return (
    <>
      {stones.map(([left,bottom,width,height,rotation], index) => (
        <View key={index} style={{
          position: 'absolute', zIndex: 6, width: width * scale,
          height: height * scale, borderRadius: 21 * scale,
          left: left * scale, bottom: bottom * scale,
          backgroundColor: index === 1 ? skin.bodyLight : skin.body,
          borderColor: skin.bodyDark, borderWidth: 3 * scale,
          transform: [{ rotate: `${rotation}deg` }],
          overflow: 'hidden',
        }}>
          <View style={{
            position: 'absolute', width: '70%', height: 5 * scale,
            left: '15%', top: 12 * scale, borderRadius: 3 * scale,
            backgroundColor: skin.accent, opacity: 0.75,
          }} />
          <View style={{
            position: 'absolute', width: 7 * scale, height: 7 * scale,
            left: 11 * scale, top: 25 * scale, borderRadius: 4 * scale,
            backgroundColor: skin.accent, opacity: 0.55,
          }} />
        </View>
      ))}
    </>
  );
}

function ChristmasPlant({ skin, scale }) {
  const segments = [
    [78,43,51,31,0],[61,68,50,31,-13],[102,72,51,31,12],
    [48,94,48,29,-22],[116,99,49,30,21],[66,120,47,29,-12],[105,126,46,28,12],
  ];
  return (
    <>
      {segments.map(([left,bottom,width,height,rotation], index) => (
        <PlantPiece key={index} style={{
          width: width * scale, height: height * scale,
          borderRadius: 13 * scale, left: left * scale,
          bottom: bottom * scale, backgroundColor: skin.body,
          borderColor: skin.bodyDark, borderWidth: 3 * scale,
          transform: [{ rotate: `${rotation}deg` }],
        }} />
      ))}
      {[44,72,111,142].map((left, index) => (
        <View key={index} style={{
          position: 'absolute', zIndex: 10, width: 21 * scale,
          height: 21 * scale, borderRadius: 11 * scale,
          left: left * scale, bottom: (90 + (index % 2) * 35) * scale,
          backgroundColor: skin.accent,
        }} />
      ))}
    </>
  );
}

function Spikes({ skin, scale, points }) {
  return (
    <>
      {points.map(([left, top], index) => (
        <View key={index} style={{
          position: 'absolute', zIndex: 10,
          left: left * scale, top: top * scale,
          width: 14 * scale, height: 8 * scale,
        }}>
          <View style={{
            position: 'absolute', left: 0, top: 3 * scale,
            width: 8 * scale, height: 2 * scale,
            backgroundColor: skin.accent,
            transform: [{ rotate: '25deg' }],
          }} />
          <View style={{
            position: 'absolute', right: 0, top: 3 * scale,
            width: 8 * scale, height: 2 * scale,
            backgroundColor: skin.accent,
            transform: [{ rotate: '-25deg' }],
          }} />
        </View>
      ))}
    </>
  );
}

function Currency({ label, value, color }) {
  return (
    <View style={styles.currencyCard}>
      <View
        style={[
          styles.currencyDot,
          { backgroundColor: color },
        ]}
      />
      <View>
        <Text style={styles.currencyValue}>
          {formatNumber(value)}
        </Text>
        <Text style={styles.currencyLabel}>{label}</Text>
      </View>
    </View>
  );
}

function Progress({ value, gold, muted }) {
  return (
    <View style={styles.progressTrack}>
      <View
        style={[
          styles.progressFill,
          gold && styles.progressGold,
          muted && styles.progressMuted,
          {
            width: `${Math.max(
              0,
              Math.min(1, Number(value) || 0)
            ) * 100}%`,
          },
        ]}
      />
    </View>
  );
}

function Stat({ label, value }) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function Statistic({ label, value }) {
  return (
    <View style={styles.statisticLine}>
      <Text style={styles.statisticLabel}>{label}</Text>
      <Text style={styles.statisticValue}>{value}</Text>
    </View>
  );
}

function Notice({ notice, onClose, onConfirm }) {
  return (
    <Modal
      visible={notice.visible}
      transparent
      animationType="fade"
      statusBarTranslucent
      onRequestClose={onClose}
    >
      <View style={styles.modalOverlay}>
        <View
          style={[
            styles.noticeCard,
            notice.type === 'danger' && styles.noticeDanger,
            notice.type === 'warning' && styles.noticeWarning,
          ]}
        >
          <View
            style={[
              styles.noticeSymbol,
              notice.type === 'danger' && styles.noticeSymbolDanger,
              notice.type === 'warning' && styles.noticeSymbolWarning,
            ]}
          >
            <Text style={styles.noticeSymbolText}>!</Text>
          </View>

          <Text style={styles.noticeTitle}>{notice.title}</Text>
          <Text style={styles.noticeMessage}>
            {notice.message}
          </Text>

          <View style={styles.noticeButtons}>
            {!!notice.cancelText && (
              <Pressable
                onPress={onClose}
                style={styles.noticeCancel}
              >
                <Text style={styles.noticeCancelText}>
                  {notice.cancelText}
                </Text>
              </Pressable>
            )}

            <Pressable
              onPress={onConfirm}
              style={[
                styles.noticeConfirm,
                notice.type === 'danger' &&
                  styles.noticeConfirmDanger,
              ]}
            >
              <Text style={styles.noticeConfirmText}>
                {notice.confirmText}
              </Text>
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
}

function numberOr(value, fallback = 0) {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function getXpNeeded(level) {
  return Math.floor(24 * Math.pow(level, 1.42));
}

function shortDecimal(value) {
  return Number(value)
    .toFixed(2)
    .replace(/\.?0+$/, '');
}

function formatNumber(value) {
  const number = Math.max(
    0,
    Math.floor(Number(value) || 0)
  );

  const units = [
    [1e15, 'kwad.'],
    [1e12, 'bln'],
    [1e9, 'mld'],
    [1e6, 'mln'],
    [1e3, 'tys.'],
  ];

  for (const [threshold, suffix] of units) {
    if (number >= threshold) {
      return `${(number / threshold)
        .toFixed(1)
        .replace('.0', '')} ${suffix}`;
    }
  }

  return String(number);
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0D1C13',
  },
  loading: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#0D1C13',
  },
  loadingText: {
    marginTop: 15,
    color: '#CBE6D1',
    fontSize: 16,
    fontWeight: '700',
  },
  content: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 48,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 13,
  },
  title: {
    color: '#FFFFFF',
    fontSize: 27,
    fontWeight: '900',
  },
  subtitle: {
    marginTop: 2,
    color: '#8EB999',
    fontSize: 14,
  },
  resetButton: {
    borderWidth: 1,
    borderColor: '#355440',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: '#172C1E',
  },
  resetButtonText: {
    color: '#C9E2CF',
    fontSize: 11,
    fontWeight: '900',
  },
  currencyRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 7,
    marginBottom: 10,
  },
  currencyCard: {
    width: '48%',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    minHeight: 54,
    borderWidth: 1,
    borderColor: '#2E4935',
    borderRadius: 14,
    paddingHorizontal: 9,
    backgroundColor: '#14291C',
  },
  currencyDot: {
    width: 14,
    height: 14,
    borderRadius: 4,
    transform: [{ rotate: '45deg' }],
  },
  currencyValue: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '900',
  },
  currencyLabel: {
    color: '#75917D',
    fontSize: 9,
  },
  levelCard: {
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#31513A',
    borderRadius: 17,
    padding: 14,
    backgroundColor: '#14291C',
  },
  levelTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 9,
  },
  levelTitle: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '800',
  },
  levelXp: {
    color: '#9DD5AA',
    fontSize: 12,
    fontWeight: '700',
  },
  progressTrack: {
    height: 9,
    overflow: 'hidden',
    borderRadius: 6,
    backgroundColor: '#253D2C',
  },
  progressFill: {
    height: '100%',
    borderRadius: 6,
    backgroundColor: '#58BE7B',
  },
  progressGold: {
    backgroundColor: '#D9AE55',
  },
  progressMuted: {
    backgroundColor: '#718078',
  },
  scoreCard: {
    borderWidth: 1,
    borderColor: '#31513A',
    borderRadius: 23,
    padding: 18,
    backgroundColor: '#163120',
  },
  scoreLabel: {
    color: '#8EB999',
    fontSize: 14,
    textAlign: 'center',
  },
  score: {
    marginTop: 3,
    color: '#FFFFFF',
    fontSize: 44,
    fontWeight: '900',
    textAlign: 'center',
  },
  statsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 17,
  },
  stat: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    color: '#B9E8C4',
    fontSize: 15,
    fontWeight: '900',
  },
  statLabel: {
    marginTop: 3,
    color: '#789482',
    fontSize: 10,
  },
  divider: {
    width: 1,
    height: 30,
    backgroundColor: '#31513A',
  },
  cactusZone: {
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 330,
  },
  cactusButton: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 225,
    height: 225,
    borderWidth: 3,
    borderColor: '#3F8E5C',
    borderRadius: 113,
    backgroundColor: '#153A25',
  },
  cactusPressed: {
    transform: [{ scale: 0.94 }],
    backgroundColor: '#1B482F',
  },
  tapText: {
    marginTop: 12,
    color: '#B6D8BE',
    fontSize: 15,
    fontWeight: '700',
  },
  comboBox: {
    alignItems: 'center',
    marginTop: 8,
    borderRadius: 12,
    paddingHorizontal: 15,
    paddingVertical: 7,
    backgroundColor: '#243F2C',
  },
  comboTitle: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '900',
  },
  comboText: {
    marginTop: 1,
    color: '#9DD5AA',
    fontSize: 10,
  },
  floatingLayer: {
    ...StyleSheet.absoluteFillObject,
    zIndex: 20,
  },
  floatText: {
    position: 'absolute',
    color: '#DDF7E3',
    fontSize: 18,
    fontWeight: '900',
  },
  floatCritical: {
    color: '#F3A65A',
  },
  floatGolden: {
    color: '#FFD166',
    fontSize: 20,
  },
  cactusCanvas: {
    position: 'relative',
  },
  plantPiece: {
    position: 'absolute',
    zIndex: 6,
  },
  cactusShadow: {
    position: 'absolute',
    backgroundColor: 'rgba(0,0,0,0.2)',
  },
  potTop: {
    position: 'absolute',
    zIndex: 5,
  },
  potBody: {
    position: 'absolute',
    zIndex: 4,
  },
  cactusMain: {
    position: 'absolute',
    zIndex: 3,
    overflow: 'hidden',
  },
  cactusHighlight: {
    position: 'absolute',
    opacity: 0.45,
  },
  cactusArmLeft: {
    position: 'absolute',
    zIndex: 2,
  },
  cactusArmLeftTop: {
    position: 'absolute',
    zIndex: 3,
  },
  cactusArmRight: {
    position: 'absolute',
    zIndex: 2,
  },
  cactusArmRightTop: {
    position: 'absolute',
    zIndex: 3,
  },
  spike: {
    position: 'absolute',
    width: 16,
    height: 8,
    zIndex: 8,
  },
  spikeLeft: {
    position: 'absolute',
    left: 0,
    top: 2,
  },
  spikeRight: {
    position: 'absolute',
    right: 0,
    top: 2,
  },
  crown: {
    position: 'absolute',
    zIndex: 10,
  },
  crownBase: {
    position: 'absolute',
  },
  crownPoint: {
    position: 'absolute',
    width: 0,
    height: 0,
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
  },
  voidCore: {
    position: 'absolute',
    zIndex: 10,
  },
  worldCard: {
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#4C4932',
    borderRadius: 20,
    padding: 15,
    backgroundColor: '#262719',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 10,
    marginBottom: 12,
  },
  sectionTitle: {
    color: '#FFFFFF',
    fontSize: 19,
    fontWeight: '900',
  },
  sectionDescription: {
    marginTop: 3,
    color: '#A9A887',
    fontSize: 12,
  },
  worldBonus: {
    color: '#E9C46A',
    fontSize: 18,
    fontWeight: '900',
  },
  nextBiome: {
    marginBottom: 8,
    color: '#E6D9A2',
    fontSize: 13,
    fontWeight: '700',
  },
  progressCaption: {
    marginTop: 6,
    color: '#9C9879',
    fontSize: 11,
    textAlign: 'right',
  },
  completeText: {
    color: '#E9C46A',
    fontSize: 14,
    fontWeight: '800',
  },
  horizontalList: {
    gap: 10,
    paddingTop: 14,
    paddingRight: 4,
  },
  biomeMasteryCard: {
    marginBottom: 13,
    borderWidth: 1,
    borderColor: '#6A5A32',
    borderRadius: 14,
    padding: 12,
    backgroundColor: '#332F1C',
  },
  biomeMasteryTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 10,
    marginBottom: 9,
  },
  biomeMasteryTitle: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '900',
  },
  biomeMasteryText: {
    maxWidth: 210,
    marginTop: 3,
    color: '#B8AD7D',
    fontSize: 10,
  },
  biomeUpgradeButton: {
    minWidth: 72,
    alignItems: 'center',
    borderRadius: 11,
    paddingHorizontal: 9,
    paddingVertical: 10,
    backgroundColor: '#4B4328',
  },
  biomeUpgradeButtonReady: {
    backgroundColor: '#D9AE55',
  },
  biomeUpgradeButtonText: {
    color: '#FFF2BE',
    fontSize: 11,
    fontWeight: '900',
  },
  biomeEmoji: {
    fontSize: 34,
  },
  biomeCard: {
    alignItems: 'center',
    width: 108,
    borderWidth: 1,
    borderColor: '#514E36',
    borderRadius: 15,
    padding: 10,
    backgroundColor: '#30301E',
  },
  biomeSelected: {
    borderColor: '#E9C46A',
    backgroundColor: '#3B3820',
  },
  biomeSymbol: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 44,
    height: 44,
    borderRadius: 22,
  },
  biomeGarden: {
    backgroundColor: '#346D46',
  },
  biomeDesert: {
    backgroundColor: '#946C36',
  },
  biomeCanyon: {
    backgroundColor: '#674D86',
  },
  biomeMoon: {
    backgroundColor: '#56647A',
  },
  biomeNebula: {
    backgroundColor: '#46336A',
  },
  biomeSymbolText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '900',
  },
  biomeName: {
    marginTop: 6,
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '800',
  },
  biomeValue: {
    marginTop: 4,
    color: '#C8BE8E',
    fontSize: 10,
    fontWeight: '700',
  },
  locked: {
    opacity: 0.42,
  },
  tabs: {
    flexDirection: 'row',
    gap: 5,
    marginBottom: 12,
    padding: 4,
    borderRadius: 15,
    backgroundColor: '#14291C',
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    borderRadius: 11,
    paddingVertical: 10,
  },
  tabActive: {
    backgroundColor: '#315B3D',
  },
  tabText: {
    color: '#76917E',
    fontSize: 11,
    fontWeight: '800',
  },
  tabTextActive: {
    color: '#FFFFFF',
  },
  list: {
    gap: 10,
  },
  rowCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 11,
    borderWidth: 1,
    borderColor: '#2E4A35',
    borderRadius: 17,
    padding: 12,
    backgroundColor: '#14291C',
  },
  emojiIcon: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 51,
    height: 51,
    borderRadius: 15,
    backgroundColor: '#203F2A',
  },
  emojiIconText: {
    fontSize: 27,
  },
  researchIcon: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 51,
    height: 51,
    borderRadius: 15,
    backgroundColor: '#332644',
  },
  researchIconText: {
    color: '#B596E8',
    fontSize: 19,
    fontWeight: '900',
  },
  flex: {
    flex: 1,
  },
  rowTitle: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '900',
  },
  rowDescription: {
    marginTop: 3,
    color: '#8DA596',
    fontSize: 11,
    lineHeight: 15,
  },
  rowLevel: {
    marginTop: 5,
    color: '#9DD5AA',
    fontSize: 11,
    fontWeight: '800',
  },
  buyButton: {
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 68,
    minHeight: 43,
    borderRadius: 12,
    paddingHorizontal: 9,
    backgroundColor: '#263D2C',
  },
  buyButtonReady: {
    backgroundColor: '#58BE7B',
  },
  buyButtonText: {
    color: '#74877A',
    fontSize: 12,
    fontWeight: '900',
  },
  buyButtonTextReady: {
    color: '#0D2516',
  },
  researchInfo: {
    borderWidth: 1,
    borderColor: '#604B7C',
    borderRadius: 16,
    padding: 14,
    backgroundColor: '#251D31',
  },
  researchInfoTitle: {
    color: '#D8C4F0',
    fontSize: 14,
    fontWeight: '900',
  },
  researchInfoText: {
    marginTop: 4,
    color: '#AD99C4',
    fontSize: 12,
  },
  seedButton: {
    minWidth: 58,
    minHeight: 43,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
    backgroundColor: '#352F25',
  },
  seedButtonReady: {
    backgroundColor: '#6B5933',
  },
  seedButtonText: {
    color: '#F3D79A',
    fontSize: 12,
    fontWeight: '900',
  },
  ascendCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 11,
    borderWidth: 1,
    borderColor: '#604B7C',
    borderRadius: 18,
    padding: 13,
    backgroundColor: '#251D31',
  },
  ascendIcon: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 54,
    height: 54,
    borderRadius: 16,
    backgroundColor: '#342345',
  },
  ascendIconText: {
    color: '#B596E8',
    fontSize: 21,
    fontWeight: '900',
  },
  ascendTitle: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '900',
  },
  ascendText: {
    marginTop: 4,
    color: '#BBA4D0',
    fontSize: 12,
  },
  arrow: {
    color: '#B596E8',
    fontSize: 34,
  },
  skinGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  skinCard: {
    alignItems: 'center',
    width: '48%',
    borderWidth: 1,
    borderColor: '#2E4A35',
    borderRadius: 18,
    padding: 12,
    backgroundColor: '#14291C',
  },
  skinSelected: {
    borderColor: '#70D49A',
    backgroundColor: '#193823',
  },
  skinName: {
    marginTop: 2,
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '900',
  },
  skinSpecies: {
    marginTop: 2,
    color: '#789482',
    fontSize: 9,
    textAlign: 'center',
  },
  skinBonus: {
    marginTop: 3,
    color: '#8EB999',
    fontSize: 11,
  },
  skinAction: {
    width: '100%',
    marginTop: 9,
    borderRadius: 10,
    paddingVertical: 8,
    backgroundColor: '#294C34',
  },
  skinActionText: {
    color: '#CFEAD5',
    fontSize: 10,
    fontWeight: '900',
    textAlign: 'center',
  },
  goalCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 11,
    borderWidth: 1,
    borderColor: '#2E4A35',
    borderRadius: 17,
    padding: 12,
    backgroundColor: '#14291C',
  },
  goalCardReady: {
    borderColor: '#58BE7B',
  },
  goalIcon: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 43,
    height: 43,
    borderRadius: 13,
    backgroundColor: '#20382A',
  },
  goalIconDone: {
    backgroundColor: '#58BE7B',
  },
  goalIconText: {
    color: '#8EB999',
    fontSize: 26,
    fontWeight: '900',
  },
  goalIconTextDone: {
    color: '#102117',
    fontSize: 20,
  },
  goalTitle: {
    marginBottom: 7,
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '800',
  },
  goalProgress: {
    marginTop: 5,
    color: '#789482',
    fontSize: 10,
  },
  goalReward: {
    alignItems: 'center',
    gap: 2,
  },
  goalRewardSymbol: {
    color: '#68D8E8',
    fontSize: 18,
  },
  goalRewardText: {
    color: '#A9E9F1',
    fontSize: 12,
    fontWeight: '900',
  },
  statisticsCard: {
    marginTop: 5,
    borderWidth: 1,
    borderColor: '#2E4A35',
    borderRadius: 18,
    padding: 15,
    backgroundColor: '#14291C',
  },
  statisticLine: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 13,
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#263E2D',
  },
  statisticLabel: {
    color: '#8DA596',
    fontSize: 12,
  },
  statisticValue: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '900',
  },
  footer: {
    marginTop: 24,
    color: '#607767',
    fontSize: 11,
    textAlign: 'center',
  },
  modalOverlay: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 23,
    backgroundColor: 'rgba(4,12,7,0.82)',
  },
  noticeCard: {
    width: '100%',
    maxWidth: 380,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#3B6547',
    borderRadius: 25,
    padding: 21,
    backgroundColor: '#15301F',
  },
  noticeDanger: {
    borderColor: '#7D3F3A',
    backgroundColor: '#301D1B',
  },
  noticeWarning: {
    borderColor: '#75613B',
    backgroundColor: '#302A1B',
  },
  noticeSymbol: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 54,
    height: 54,
    marginBottom: 8,
    borderWidth: 2,
    borderColor: '#70D49A',
    borderRadius: 27,
    backgroundColor: '#244B30',
  },
  noticeSymbolDanger: {
    borderColor: '#E07268',
    backgroundColor: '#4A2522',
  },
  noticeSymbolWarning: {
    borderColor: '#E9C46A',
    backgroundColor: '#4A3D22',
  },
  noticeSymbolText: {
    color: '#FFFFFF',
    fontSize: 27,
    fontWeight: '900',
  },
  noticeTitle: {
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: '900',
    textAlign: 'center',
  },
  noticeMessage: {
    marginTop: 9,
    color: '#B6CCBC',
    fontSize: 13,
    lineHeight: 20,
    textAlign: 'center',
  },
  noticeButtons: {
    flexDirection: 'row',
    width: '100%',
    gap: 9,
    marginTop: 20,
  },
  noticeCancel: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 47,
    borderWidth: 1,
    borderColor: '#45624E',
    borderRadius: 13,
  },
  noticeCancelText: {
    color: '#C8D9CC',
    fontSize: 13,
    fontWeight: '800',
  },
  noticeConfirm: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 47,
    borderRadius: 13,
    backgroundColor: '#58BE7B',
  },
  noticeConfirmDanger: {
    backgroundColor: '#D2675D',
  },
  noticeConfirmText: {
    color: '#102117',
    fontSize: 13,
    fontWeight: '900',
  },
});
