// Comprehensive mapping for Indian agricultural commodities
// Contains Telugu translations, categories, clean names, and verified high-resolution Unsplash photos

export interface CropInfo {
  nameEn: string;
  nameTe: string;
  category: 'Vegetables' | 'Grains' | 'Pulses' | 'Fruits' | 'Commercial' | 'Spices' | 'Oilseeds';
  imageUrl: string;
}

export const CROP_CATALOG: Record<string, CropInfo> = {
  tomato: {
    nameEn: 'Tomato',
    nameTe: 'టమాట',
    category: 'Vegetables',
    imageUrl: 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?auto=format&fit=crop&w=600&q=80',
  },
  potato: {
    nameEn: 'Potato',
    nameTe: 'బంగాళాదుంప',
    category: 'Vegetables',
    imageUrl: 'https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=600&q=80',
  },
  onion: {
    nameEn: 'Onion',
    nameTe: 'ఉల్లిపాయ',
    category: 'Vegetables',
    imageUrl: 'https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?auto=format&fit=crop&w=600&q=80',
  },
  chilli: {
    nameEn: 'Green Chilli',
    nameTe: 'పచ్చి మిర్చి',
    category: 'Vegetables',
    imageUrl: 'https://images.unsplash.com/photo-1588252303782-cb80119abd6d?auto=format&fit=crop&w=600&q=80',
  },
  'dry chilli': {
    nameEn: 'Dry Chillies',
    nameTe: 'ఎండు మిర్చి',
    category: 'Spices',
    imageUrl: 'https://images.unsplash.com/photo-1565557623262-b51c2513a641?auto=format&fit=crop&w=600&q=80',
  },
  cauliflower: {
    nameEn: 'Cauliflower',
    nameTe: 'కాలిఫ్లవర్',
    category: 'Vegetables',
    imageUrl: 'https://images.unsplash.com/photo-1568584711075-3d021a7c3ca3?auto=format&fit=crop&w=600&q=80',
  },
  cabbage: {
    nameEn: 'Cabbage',
    nameTe: 'క్యాబేజీ',
    category: 'Vegetables',
    imageUrl: 'https://images.unsplash.com/photo-1592451336423-7182280d507f?auto=format&fit=crop&w=600&q=80',
  },
  carrot: {
    nameEn: 'Carrot',
    nameTe: 'క్యారెట్',
    category: 'Vegetables',
    imageUrl: 'https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?auto=format&fit=crop&w=600&q=80',
  },
  beetroot: {
    nameEn: 'Beetroot',
    nameTe: 'బీట్రూట్',
    category: 'Vegetables',
    imageUrl: 'https://images.unsplash.com/photo-1526470608268-f674ce90ebd4?auto=format&fit=crop&w=600&q=80',
  },
  brinjal: {
    nameEn: 'Brinjal',
    nameTe: 'వంకాయ',
    category: 'Vegetables',
    imageUrl: 'https://images.unsplash.com/photo-1618164435735-413d3b066ce4?auto=format&fit=crop&w=600&q=80',
  },
  capsicum: {
    nameEn: 'Capsicum',
    nameTe: 'క్యాప్సికమ్',
    category: 'Vegetables',
    imageUrl: 'https://images.unsplash.com/photo-1563514088019-389f4eb1202e?auto=format&fit=crop&w=600&q=80',
  },
  bhindi: {
    nameEn: 'Ladies Finger (Bhindi)',
    nameTe: 'బెండకాయ',
    category: 'Vegetables',
    imageUrl: 'https://images.unsplash.com/photo-1425543103986-22abb7d7e8d2?auto=format&fit=crop&w=600&q=80',
  },
  drumstick: {
    nameEn: 'Drumstick (Moringa)',
    nameTe: 'ములక్కాడ',
    category: 'Vegetables',
    imageUrl: 'https://images.unsplash.com/photo-1628088062854-d1870b4553da?auto=format&fit=crop&w=600&q=80',
  },
  'bottle gourd': {
    nameEn: 'Bottle Gourd (Sorakaya)',
    nameTe: 'సొరకాయ',
    category: 'Vegetables',
    imageUrl: 'https://images.unsplash.com/photo-1597362925123-77861d3fbac7?auto=format&fit=crop&w=600&q=80',
  },
  'bitter gourd': {
    nameEn: 'Bitter Gourd (Kakarakaya)',
    nameTe: 'కాకరకాయ',
    category: 'Vegetables',
    imageUrl: 'https://images.unsplash.com/photo-1601004890684-d8cbf643f5f2?auto=format&fit=crop&w=600&q=80',
  },
  'ridge gourd': {
    nameEn: 'Ridge Gourd (Beerakaya)',
    nameTe: 'బీరకాయ',
    category: 'Vegetables',
    imageUrl: 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?auto=format&fit=crop&w=600&q=80',
  },
  cucumber: {
    nameEn: 'Cucumber (Dosakaya)',
    nameTe: 'దోసకాయ',
    category: 'Vegetables',
    imageUrl: 'https://images.unsplash.com/photo-1449300079323-02e209d9d3a6?auto=format&fit=crop&w=600&q=80',
  },
  'little gourd': {
    nameEn: 'Little Gourd (Dondakaya)',
    nameTe: 'దొండకాయ',
    category: 'Vegetables',
    imageUrl: 'https://images.unsplash.com/photo-1590779033100-9f60a05a013d?auto=format&fit=crop&w=600&q=80',
  },
  thondekai: {
    nameEn: 'Thondekai (Kundru)',
    nameTe: 'దొండకాయ',
    category: 'Vegetables',
    imageUrl: 'https://images.unsplash.com/photo-1590779033100-9f60a05a013d?auto=format&fit=crop&w=600&q=80',
  },
  colacasia: {
    nameEn: 'Colacasia (Chamadumpa)',
    nameTe: 'చామదుంప',
    category: 'Vegetables',
    imageUrl: 'https://images.unsplash.com/photo-1587049352847-4a222e784d38?auto=format&fit=crop&w=600&q=80',
  },
  radish: {
    nameEn: 'Radish (Mullangi)',
    nameTe: 'ముల్లంగి',
    category: 'Vegetables',
    imageUrl: 'https://images.unsplash.com/photo-1593952745300-8438bbdf5011?auto=format&fit=crop&w=600&q=80',
  },
  ginger: {
    nameEn: 'Ginger (Allam)',
    nameTe: 'అల్లం',
    category: 'Spices',
    imageUrl: 'https://images.unsplash.com/photo-1615485500704-8e990f9900f7?auto=format&fit=crop&w=600&q=80',
  },
  garlic: {
    nameEn: 'Garlic (Vellulli)',
    nameTe: 'వెల్లుల్లి',
    category: 'Spices',
    imageUrl: 'https://images.unsplash.com/photo-1540148426945-6cf22a6b2383?auto=format&fit=crop&w=600&q=80',
  },
  turmeric: {
    nameEn: 'Turmeric (Pasupu)',
    nameTe: 'పసుపు',
    category: 'Spices',
    imageUrl: 'https://images.unsplash.com/photo-1615485925600-97237c4fc1ec?auto=format&fit=crop&w=600&q=80',
  },
  paddy: {
    nameEn: 'Paddy / Rice (Vari)',
    nameTe: 'వరి (ధాన్యం)',
    category: 'Grains',
    imageUrl: 'https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=600&q=80',
  },
  cotton: {
    nameEn: 'Raw Cotton (Patti)',
    nameTe: 'పత్తి',
    category: 'Commercial',
    imageUrl: 'https://images.unsplash.com/photo-1606041008023-472dfb5e530f?auto=format&fit=crop&w=600&q=80',
  },
  maize: {
    nameEn: 'Maize (Mokkajonna)',
    nameTe: 'మొక్కజొన్న',
    category: 'Grains',
    imageUrl: 'https://images.unsplash.com/photo-1551754655-cd27e38d2076?auto=format&fit=crop&w=600&q=80',
  },
  groundnut: {
    nameEn: 'Groundnut (Verusenaga)',
    nameTe: 'వేరుశనగ (పల్లీ)',
    category: 'Oilseeds',
    imageUrl: 'https://images.unsplash.com/photo-1567892328521-9eb128148b30?auto=format&fit=crop&w=600&q=80',
  },
  'bengal gram': {
    nameEn: 'Bengal Gram (Senagalu)',
    nameTe: 'శనగలు',
    category: 'Pulses',
    imageUrl: 'https://images.unsplash.com/photo-1515543237350-b3eea1ec8082?auto=format&fit=crop&w=600&q=80',
  },
  'red gram': {
    nameEn: 'Red Gram / Toor (Kandulu)',
    nameTe: 'కందులు',
    category: 'Pulses',
    imageUrl: 'https://images.unsplash.com/photo-1585994192701-f1a505c8574a?auto=format&fit=crop&w=600&q=80',
  },
  'green gram': {
    nameEn: 'Green Gram / Moong (Pesaralu)',
    nameTe: 'పెసలు',
    category: 'Pulses',
    imageUrl: 'https://images.unsplash.com/photo-1585994192701-f1a505c8574a?auto=format&fit=crop&w=600&q=80',
  },
  'black gram': {
    nameEn: 'Black Gram / Urad (Minumulu)',
    nameTe: 'మినుములు',
    category: 'Pulses',
    imageUrl: 'https://images.unsplash.com/photo-1585994192701-f1a505c8574a?auto=format&fit=crop&w=600&q=80',
  },
  lemon: {
    nameEn: 'Lemon (Nimmakaya)',
    nameTe: 'నిమ్మకాయ',
    category: 'Fruits',
    imageUrl: 'https://images.unsplash.com/photo-1590848665042-4f3dfbe6fcb8?auto=format&fit=crop&w=600&q=80',
  },
  banana: {
    nameEn: 'Banana (Arati)',
    nameTe: 'అరటిపండు',
    category: 'Fruits',
    imageUrl: 'https://images.unsplash.com/photo-1571501679680-de32f1e7aad4?auto=format&fit=crop&w=600&q=80',
  },
  mango: {
    nameEn: 'Mango (Mamidi)',
    nameTe: 'మామిడి',
    category: 'Fruits',
    imageUrl: 'https://images.unsplash.com/photo-1553279768-865429fa0078?auto=format&fit=crop&w=600&q=80',
  },
  papaya: {
    nameEn: 'Papaya (Boppayi)',
    nameTe: 'బొప్పాయి',
    category: 'Fruits',
    imageUrl: 'https://images.unsplash.com/photo-1517282009859-f000ec3b26fe?auto=format&fit=crop&w=600&q=80',
  },
  watermelon: {
    nameEn: 'Watermelon (Puchakaya)',
    nameTe: 'పుచ్చకాయ',
    category: 'Fruits',
    imageUrl: 'https://images.unsplash.com/photo-1587049352846-4a222e784d38?auto=format&fit=crop&w=600&q=80',
  },
  soyabean: {
    nameEn: 'Soyabean',
    nameTe: 'సోయాబీన్',
    category: 'Oilseeds',
    imageUrl: 'https://images.unsplash.com/photo-1599940824399-b87987ceb72a?auto=format&fit=crop&w=600&q=80',
  },
  wheat: {
    nameEn: 'Wheat (Godhumalu)',
    nameTe: 'గోధుమలు',
    category: 'Grains',
    imageUrl: 'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&w=600&q=80',
  },
  coconut: {
    nameEn: 'Coconut (Kobbari)',
    nameTe: 'కొబ్బరికాయ',
    category: 'Commercial',
    imageUrl: 'https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&w=600&q=80',
  },
};

export const DEFAULT_CROP_IMAGE = 'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=600&q=80';

/**
 * Intelligent crop resolver that handles all AGMARKNET naming quirks
 */
export function resolveCropMetadata(rawCommodity: string): CropInfo {
  if (!rawCommodity) {
    return {
      nameEn: 'Agricultural Produce',
      nameTe: 'వ్యవసాయ పంట',
      category: 'Vegetables',
      imageUrl: DEFAULT_CROP_IMAGE,
    };
  }

  const clean = rawCommodity.toLowerCase().trim();

  // Exact & Keyword Checks
  if (clean.includes('tomato')) return CROP_CATALOG.tomato;
  if (clean.includes('potato') || clean.includes('aloo') || clean.includes('bangaladumpa')) return CROP_CATALOG.potato;
  if (clean.includes('onion') || clean.includes('pyaz') || clean.includes('ullipaya')) return CROP_CATALOG.onion;
  if (clean.includes('dry chilli') || clean.includes('dry chillies') || clean.includes('endu mirchi')) return CROP_CATALOG['dry chilli'];
  if (clean.includes('green chilli') || clean.includes('chilli') || clean.includes('mirchi') || clean.includes('chili')) return CROP_CATALOG.chilli;
  if (clean.includes('cauliflower') || clean.includes('gobi')) return CROP_CATALOG.cauliflower;
  if (clean.includes('cabbage') || clean.includes('patta')) return CROP_CATALOG.cabbage;
  if (clean.includes('carrot') || clean.includes('gajar')) return CROP_CATALOG.carrot;
  if (clean.includes('beetroot')) return CROP_CATALOG.beetroot;
  if (clean.includes('brinjal') || clean.includes('eggplant') || clean.includes('baingan') || clean.includes('vankaya')) return CROP_CATALOG.brinjal;
  if (clean.includes('capsicum') || clean.includes('shimla')) return CROP_CATALOG.capsicum;
  if (clean.includes('bhindi') || clean.includes('ladies finger') || clean.includes('okra') || clean.includes('bendakaya')) return CROP_CATALOG.bhindi;
  if (clean.includes('drumstick') || clean.includes('moringa') || clean.includes('mulakkada') || clean.includes('saijan')) return CROP_CATALOG.drumstick;
  if (clean.includes('bottle gourd') || clean.includes('lauki') || clean.includes('sorakaya')) return CROP_CATALOG['bottle gourd'];
  if (clean.includes('bitter gourd') || clean.includes('karela') || clean.includes('kakarakaya')) return CROP_CATALOG['bitter gourd'];
  if (clean.includes('ridge') || clean.includes('tori') || clean.includes('beerakaya')) return CROP_CATALOG['ridge gourd'];
  if (clean.includes('cucum') || clean.includes('kheera') || clean.includes('dosakaya')) return CROP_CATALOG.cucumber;
  if (clean.includes('little gourd') || clean.includes('kundru') || clean.includes('dondakaya')) return CROP_CATALOG['little gourd'];
  if (clean.includes('thondekai') || clean.includes('tindora')) return CROP_CATALOG.thondekai;
  if (clean.includes('colacasia') || clean.includes('arbi') || clean.includes('chamadumpa') || clean.includes('taro')) return CROP_CATALOG.colacasia;
  if (clean.includes('radish') || clean.includes('mooli') || clean.includes('mullangi')) return CROP_CATALOG.radish;
  if (clean.includes('ginger') || clean.includes('adrak') || clean.includes('allam')) return CROP_CATALOG.ginger;
  if (clean.includes('garlic') || clean.includes('lahsun') || clean.includes('vellulli')) return CROP_CATALOG.garlic;
  if (clean.includes('turmeric') || clean.includes('haldi') || clean.includes('pasupu')) return CROP_CATALOG.turmeric;
  if (clean.includes('paddy') || clean.includes('dhan') || clean.includes('rice') || clean.includes('vari')) return CROP_CATALOG.paddy;
  if (clean.includes('cotton') || clean.includes('kapas') || clean.includes('patti')) return CROP_CATALOG.cotton;
  if (clean.includes('maize') || clean.includes('corn') || clean.includes('makka') || clean.includes('mokkajonna')) return CROP_CATALOG.maize;
  if (clean.includes('groundnut') || clean.includes('peanut') || clean.includes('palli') || clean.includes('verusenaga')) return CROP_CATALOG.groundnut;
  if (clean.includes('bengal gram') || clean.includes('chana') || clean.includes('senagalu')) return CROP_CATALOG['bengal gram'];
  if (clean.includes('red gram') || clean.includes('arhar') || clean.includes('tur') || clean.includes('toor') || clean.includes('kandulu')) return CROP_CATALOG['red gram'];
  if (clean.includes('green gram') || clean.includes('moong') || clean.includes('pesaralu')) return CROP_CATALOG['green gram'];
  if (clean.includes('black gram') || clean.includes('urad') || clean.includes('minumulu')) return CROP_CATALOG['black gram'];
  if (clean.includes('lemon') || clean.includes('nimbu') || clean.includes('nimmakaya')) return CROP_CATALOG.lemon;
  if (clean.includes('banana') || clean.includes('kela') || clean.includes('arati')) return CROP_CATALOG.banana;
  if (clean.includes('mango') || clean.includes('aam') || clean.includes('mamidi')) return CROP_CATALOG.mango;
  if (clean.includes('papaya') || clean.includes('papita') || clean.includes('boppayi')) return CROP_CATALOG.papaya;
  if (clean.includes('watermelon') || clean.includes('tarbooz') || clean.includes('pucha')) return CROP_CATALOG.watermelon;
  if (clean.includes('soya') || clean.includes('soyabean')) return CROP_CATALOG.soyabean;
  if (clean.includes('wheat') || clean.includes('gehun') || clean.includes('godhumalu')) return CROP_CATALOG.wheat;
  if (clean.includes('coconut') || clean.includes('nariyal') || clean.includes('kobbari')) return CROP_CATALOG.coconut;

  // Fallback for any unknown commodity
  return {
    nameEn: rawCommodity,
    nameTe: rawCommodity,
    category: 'Vegetables',
    imageUrl: DEFAULT_CROP_IMAGE,
  };
}
