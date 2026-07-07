/**
 * FitScale™ App - Body Mass Index Dashboard Core Logic
 */

// --- Nomogram Background Plugin ---
const nomogramBmiPlugin = {
  id: 'nomogramBmi',
  beforeDatasetsDraw(chart) {
    const { ctx, chartArea: { top, bottom, left, right }, scales: { x, y } } = chart;
    ctx.save();
    
    // Draw columns of pixels from left to right to shade the BMI zones
    for (let px = left; px <= right; px++) {
      const heightCm = x.getValueForPixel(px);
      const heightM = heightCm / 100;
      if (heightM <= 0) continue;
      
      const h2 = heightM * heightM;
      
      // Calculate weight boundaries in kg
      const w18_5 = 18.5 * h2;
      const w25 = 25 * h2;
      const w30 = 30 * h2;
      
      // Convert weights to Y pixel values, clamping to the chart area
      const py18_5 = Math.max(top, Math.min(bottom, y.getPixelForValue(w18_5)));
      const py25 = Math.max(top, Math.min(bottom, y.getPixelForValue(w25)));
      const py30 = Math.max(top, Math.min(bottom, y.getPixelForValue(w30)));
      
      // 1. Underweight zone (bottom of chart up to py18_5)
      ctx.fillStyle = 'rgba(59, 130, 246, 0.12)';
      ctx.fillRect(px, py18_5, 1, bottom - py18_5);
      
      // 2. Normal zone (py18_5 up to py25)
      ctx.fillStyle = 'rgba(16, 185, 129, 0.12)';
      ctx.fillRect(px, py25, 1, py18_5 - py25);
      
      // 3. Overweight zone (py25 up to py30)
      ctx.fillStyle = 'rgba(245, 158, 11, 0.12)';
      ctx.fillRect(px, py30, 1, py25 - py30);
      
      // 4. Obese zone (py30 up to top of chart)
      ctx.fillStyle = 'rgba(239, 68, 68, 0.12)';
      ctx.fillRect(px, top, 1, py30 - top);
    }
    
    // Draw thin boundary curve lines
    ctx.lineWidth = 1.5;
    
    // BMI 18.5 Curve
    ctx.strokeStyle = 'rgba(59, 130, 246, 0.3)';
    ctx.beginPath();
    for (let px = left; px <= right; px++) {
      const hM = x.getValueForPixel(px) / 100;
      const w = 18.5 * hM * hM;
      const py = y.getPixelForValue(w);
      if (px === left) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();

    // BMI 25.0 Curve
    ctx.strokeStyle = 'rgba(16, 185, 129, 0.3)';
    ctx.beginPath();
    for (let px = left; px <= right; px++) {
      const hM = x.getValueForPixel(px) / 100;
      const w = 25 * hM * hM;
      const py = y.getPixelForValue(w);
      if (px === left) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();

    // BMI 30.0 Curve
    ctx.strokeStyle = 'rgba(239, 68, 68, 0.3)';
    ctx.beginPath();
    for (let px = left; px <= right; px++) {
      const hM = x.getValueForPixel(px) / 100;
      const w = 30 * hM * hM;
      const py = y.getPixelForValue(w);
      if (px === left) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();
    
    ctx.restore();
  }
};

// --- Application State ---
const state = {
  currentUnit: 'metric', // 'metric' or 'imperial'
  gender: 'male',
  heightCm: 175,
  heightFt: 5,
  heightIn: 9,
  weightKg: 70,
  weightLb: 154.3,
  age: 28,
  activity: 1.375,
  targetWeight: null, // in kg
  logs: [],
  editingLogId: null
};

// --- Constants & Selectors ---
const GAUGE_CIRCUMFERENCE = 125.66; // pi * 40
let nomogramChart = null;
let trendChart = null;

// --- DOM Elements ---
const themeToggle = document.getElementById('theme-toggle');
const loadSampleBtn = document.getElementById('load-sample-btn');
const unitTabs = document.querySelectorAll('.unit-tab');
const bmiForm = document.getElementById('bmi-form');
const genderRadios = document.getElementsByName('gender');

const metricHeightGroup = document.getElementById('metric-height-group');
const imperialHeightGroup = document.getElementById('imperial-height-group');
const heightCmSlider = document.getElementById('height-cm');
const heightCmNum = document.getElementById('height-cm-num');
const heightCmVal = document.getElementById('height-cm-val');
const heightFtInput = document.getElementById('height-ft');
const heightInInput = document.getElementById('height-in');

const metricWeightGroup = document.getElementById('metric-weight-group');
const imperialWeightGroup = document.getElementById('imperial-weight-group');
const weightKgSlider = document.getElementById('weight-kg');
const weightKgNum = document.getElementById('weight-kg-num');
const weightKgVal = document.getElementById('weight-kg-val');
const weightLbSlider = document.getElementById('weight-lb');
const weightLbNum = document.getElementById('weight-lb-num');
const weightLbVal = document.getElementById('weight-lb-val');

const ageInput = document.getElementById('age');
const activitySelect = document.getElementById('activity');
const targetWeightInput = document.getElementById('target-weight');
const targetWeightBadge = document.getElementById('target-weight-badge');
const targetWeightUnit = document.getElementById('target-weight-unit');
const clearTargetBtn = document.getElementById('clear-target-btn');

const calculateBtn = document.getElementById('calculate-btn');
const saveLogBtn = document.getElementById('save-log-btn');

// Results elements
const bmiDisplay = document.getElementById('bmi-display');
const bmiCategoryDisplay = document.getElementById('bmi-category-display');
const gaugeFill = document.getElementById('gauge-fill');
const gaugeNeedle = document.getElementById('gauge-needle');
const targetStatusVal = document.getElementById('target-status-val');
const targetStatusSub = document.getElementById('target-status-sub');
const idealRangeVal = document.getElementById('ideal-range-val');
const idealRangeHeight = document.getElementById('ideal-range-height');
const bmrVal = document.getElementById('bmr-val');
const tdeeVal = document.getElementById('tdee-val');

// Chart view controls
const chartTabs = document.querySelectorAll('.chart-tab');
const nomogramContainer = document.getElementById('nomogram-container');
const trendContainer = document.getElementById('trend-container');

// Insights & Logs
const insightsText = document.getElementById('insights-text');
const historyBody = document.getElementById('history-body');
const exportJsonBtn = document.getElementById('export-json-btn');
const importTriggerBtn = document.getElementById('import-trigger-btn');
const importFile = document.getElementById('import-file');
const clearAllBtn = document.getElementById('clear-all-btn');

// --- Helper Functions ---
function cmToFtIn(cm) {
  const inches = cm / 2.54;
  const ft = Math.floor(inches / 12);
  const inc = Math.round(inches % 12);
  return { ft, in: inc === 12 ? 0 : inc };
}

function ftInToCm(ft, inches) {
  return (ft * 12 + inches) * 2.54;
}

function kgToLb(kg) {
  return kg * 2.20462;
}

function lbToKg(lb) {
  return lb / 2.20462;
}

function formatNumber(num, decimals = 1) {
  return Number(num).toFixed(decimals);
}

// --- Local Storage Management ---
function loadFromStorage() {
  const saved = localStorage.getItem('fitscale_state');
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      state.currentUnit = parsed.currentUnit || 'metric';
      state.gender = parsed.gender || 'male';
      state.heightCm = parsed.heightCm || 175;
      state.weightKg = parsed.weightKg || 70;
      state.age = parsed.age || 28;
      state.activity = parsed.activity || 1.375;
      state.targetWeight = parsed.targetWeight || null;
      state.logs = parsed.logs || [];
      
      // Update other temporary height/weight variables based on loaded metric ones
      const imperialH = cmToFtIn(state.heightCm);
      state.heightFt = imperialH.ft;
      state.heightIn = imperialH.in;
      state.weightLb = kgToLb(state.weightKg);
    } catch (e) {
      console.error("Error parsing saved state", e);
    }
  }
}

function saveToStorage() {
  localStorage.setItem('fitscale_state', JSON.stringify({
    currentUnit: state.currentUnit,
    gender: state.gender,
    heightCm: state.heightCm,
    weightKg: state.weightKg,
    age: state.age,
    activity: state.activity,
    targetWeight: state.targetWeight,
    logs: state.logs
  }));
}

// --- Calculations ---
function getBmiDetails(heightCm, weightKg) {
  const heightM = heightCm / 100;
  const bmi = weightKg / (heightM * heightM);
  
  let category = '';
  let colorClass = '';
  let bulletClass = '';
  
  if (bmi < 18.5) {
    category = 'Underweight';
    colorClass = 'text-underweight';
    bulletClass = 'bullet-underweight';
  } else if (bmi < 25) {
    category = 'Normal';
    colorClass = 'text-normal';
    bulletClass = 'bullet-normal';
  } else if (bmi < 30) {
    category = 'Overweight';
    colorClass = 'text-overweight';
    bulletClass = 'bullet-warning';
  } else {
    category = 'Obese';
    colorClass = 'text-obese';
    bulletClass = 'bullet-danger';
  }
  
  return { bmi, category, colorClass, bulletClass };
}

function getBmr(weightKg, heightCm, age, gender) {
  // Mifflin-St Jeor Equation
  if (gender === 'male') {
    return 10 * weightKg + 6.25 * heightCm - 5 * age + 5;
  } else {
    return 10 * weightKg + 6.25 * heightCm - 5 * age - 161;
  }
}

// --- UI Updates ---

// Sync sliders and number fields
function syncHeightInputs(source) {
  if (source === 'slider') {
    const cm = parseInt(heightCmSlider.value);
    state.heightCm = cm;
    heightCmNum.value = cm;
    heightCmVal.textContent = `${cm} cm`;
  } else if (source === 'number') {
    let cm = parseInt(heightCmNum.value);
    if (isNaN(cm)) cm = 170;
    cm = Math.max(100, Math.min(250, cm));
    state.heightCm = cm;
    heightCmSlider.value = cm;
    heightCmVal.textContent = `${cm} cm`;
  } else if (source === 'imperial') {
    const ft = parseInt(heightFtInput.value) || 0;
    const inch = parseInt(heightInInput.value) || 0;
    state.heightFt = ft;
    state.heightIn = inch;
    state.heightCm = ftInToCm(ft, inch);
    heightCmSlider.value = Math.round(state.heightCm);
    heightCmNum.value = Math.round(state.heightCm);
    heightCmVal.textContent = `${Math.round(state.heightCm)} cm`;
  }
}

function syncWeightInputs(source) {
  if (source === 'slider-metric') {
    const kg = parseFloat(weightKgSlider.value);
    state.weightKg = kg;
    weightKgNum.value = kg;
    weightKgVal.textContent = `${formatNumber(kg, 1)} kg`;
    state.weightLb = kgToLb(kg);
    weightLbSlider.value = Math.round(state.weightLb);
    weightLbNum.value = formatNumber(state.weightLb, 1);
    weightLbVal.textContent = `${formatNumber(state.weightLb, 1)} lbs`;
  } else if (source === 'number-metric') {
    let kg = parseFloat(weightKgNum.value);
    if (isNaN(kg)) kg = 70;
    kg = Math.max(20, Math.min(250, kg));
    state.weightKg = kg;
    weightKgSlider.value = kg;
    weightKgVal.textContent = `${formatNumber(kg, 1)} kg`;
    state.weightLb = kgToLb(kg);
    weightLbSlider.value = Math.round(state.weightLb);
    weightLbNum.value = formatNumber(state.weightLb, 1);
    weightLbVal.textContent = `${formatNumber(state.weightLb, 1)} lbs`;
  } else if (source === 'slider-imperial') {
    const lb = parseFloat(weightLbSlider.value);
    state.weightLb = lb;
    weightLbNum.value = lb;
    weightLbVal.textContent = `${formatNumber(lb, 1)} lbs`;
    state.weightKg = lbToKg(lb);
    weightKgSlider.value = state.weightKg;
    weightKgNum.value = formatNumber(state.weightKg, 1);
    weightKgVal.textContent = `${formatNumber(state.weightKg, 1)} kg`;
  } else if (source === 'number-imperial') {
    let lb = parseFloat(weightLbNum.value);
    if (isNaN(lb)) lb = 150;
    lb = Math.max(40, Math.min(550, lb));
    state.weightLb = lb;
    weightLbSlider.value = lb;
    weightLbVal.textContent = `${formatNumber(lb, 1)} lbs`;
    state.weightKg = lbToKg(lb);
    weightKgSlider.value = state.weightKg;
    weightKgNum.value = formatNumber(state.weightKg, 1);
    weightKgVal.textContent = `${formatNumber(state.weightKg, 1)} kg`;
  }
}

function updateUnitTabUI() {
  unitTabs.forEach(tab => {
    if (tab.dataset.unit === state.currentUnit) {
      tab.classList.add('active');
    } else {
      tab.classList.remove('active');
    }
  });

  // Switch form input fields visibility
  if (state.currentUnit === 'metric') {
    metricHeightGroup.classList.remove('hidden');
    imperialHeightGroup.classList.add('hidden');
    metricWeightGroup.classList.remove('hidden');
    imperialWeightGroup.classList.add('hidden');
    targetWeightUnit.textContent = 'kg';
    if (state.targetWeight) {
      targetWeightInput.value = formatNumber(state.targetWeight, 1);
      targetWeightBadge.textContent = `${formatNumber(state.targetWeight, 1)} kg`;
      targetWeightBadge.classList.remove('badge-neutral');
    } else {
      targetWeightInput.value = '';
      targetWeightBadge.textContent = 'None';
      targetWeightBadge.classList.add('badge-neutral');
    }
  } else {
    metricHeightGroup.classList.add('hidden');
    imperialHeightGroup.classList.remove('hidden');
    metricWeightGroup.classList.add('hidden');
    imperialWeightGroup.classList.remove('hidden');
    targetWeightUnit.textContent = 'lbs';
    if (state.targetWeight) {
      const targetLbs = kgToLb(state.targetWeight);
      targetWeightInput.value = formatNumber(targetLbs, 1);
      targetWeightBadge.textContent = `${formatNumber(targetLbs, 1)} lbs`;
      targetWeightBadge.classList.remove('badge-neutral');
    } else {
      targetWeightInput.value = '';
      targetWeightBadge.textContent = 'None';
      targetWeightBadge.classList.add('badge-neutral');
    }
    
    // Sync imperial inputs
    const imperialH = cmToFtIn(state.heightCm);
    heightFtInput.value = imperialH.ft;
    heightInInput.value = imperialH.in;
  }
}

function updateDashboardUI() {
  const { bmi, category, colorClass } = getBmiDetails(state.heightCm, state.weightKg);

  // 1. Update BMI and category texts
  bmiDisplay.textContent = formatNumber(bmi, 1);
  bmiCategoryDisplay.textContent = category;
  
  // Update colors
  bmiCategoryDisplay.className = `bmi-label ${colorClass}`;
  
  // 2. Update Gauge fill and needle angle
  // Map BMI 15 -> 0%, BMI 35 -> 100%
  let percent = (bmi - 15) / 20;
  percent = Math.max(0, Math.min(1, percent));
  
  // Semi-circle circumference is 125.66
  const offset = GAUGE_CIRCUMFERENCE * (1 - percent);
  gaugeFill.style.strokeDashoffset = offset;
  
  // Set correct color class on the gauge fill path
  gaugeFill.className.baseVal = `gauge-fill val-${category.toLowerCase()}`;
  
  // Needle rotation (-90deg on left to 90deg on right)
  const angle = -90 + percent * 180;
  gaugeNeedle.style.transform = `rotate(${angle}deg)`;
  
  // Match colors of gauge elements
  let activeColor = '#10b981'; // normal
  if (category === 'Underweight') activeColor = '#3b82f6';
  if (category === 'Overweight') activeColor = '#f59e0b';
  if (category === 'Obese') activeColor = '#ef4444';
  
  gaugeNeedle.setAttribute('stroke', activeColor);
  document.getElementById('gauge-pin').setAttribute('fill', activeColor);

  // 3. Update Mini Cards
  // Card A: Target status
  if (state.targetWeight) {
    const diff = state.weightKg - state.targetWeight;
    const unitText = state.currentUnit === 'metric' ? 'kg' : 'lbs';
    const dispWeight = state.currentUnit === 'metric' ? Math.abs(diff) : Math.abs(kgToLb(diff));
    const targetDispVal = state.currentUnit === 'metric' ? state.targetWeight : kgToLb(state.targetWeight);
    
    if (diff > 0.1) {
      targetStatusVal.textContent = `-${formatNumber(dispWeight, 1)} ${unitText}`;
      targetStatusVal.className = 'mini-card-val text-overweight-ui';
      targetStatusSub.textContent = `To reach target (${formatNumber(targetDispVal, 1)} ${unitText})`;
    } else if (diff < -0.1) {
      targetStatusVal.textContent = `+${formatNumber(dispWeight, 1)} ${unitText}`;
      targetStatusVal.className = 'mini-card-val text-underweight-ui';
      targetStatusSub.textContent = `To reach target (${formatNumber(targetDispVal, 1)} ${unitText})`;
    } else {
      targetStatusVal.textContent = 'Goal Met!';
      targetStatusVal.className = 'mini-card-val text-normal-ui';
      targetStatusSub.textContent = `Weight matches goal (${formatNumber(targetDispVal, 1)} ${unitText})`;
    }
  } else {
    targetStatusVal.textContent = '- -';
    targetStatusVal.className = 'mini-card-val';
    targetStatusSub.textContent = 'Set a goal weight';
  }

  // Card B: Ideal Weight Range
  const minIdealKg = 18.5 * (state.heightCm / 100) ** 2;
  const maxIdealKg = 24.9 * (state.heightCm / 100) ** 2;
  
  if (state.currentUnit === 'metric') {
    idealRangeVal.textContent = `${formatNumber(minIdealKg, 1)} - ${formatNumber(maxIdealKg, 1)} kg`;
    idealRangeHeight.textContent = `${Math.round(state.heightCm)} cm`;
  } else {
    const minIdealLb = kgToLb(minIdealKg);
    const maxIdealLb = kgToLb(maxIdealKg);
    idealRangeVal.textContent = `${formatNumber(minIdealLb, 1)} - ${formatNumber(maxIdealLb, 1)} lbs`;
    const imperialH = cmToFtIn(state.heightCm);
    idealRangeHeight.textContent = `${imperialH.ft}'${imperialH.in}"`;
  }

  // Card C & D: BMR & TDEE
  const bmr = getBmr(state.weightKg, state.heightCm, state.age, state.gender);
  const tdee = bmr * state.activity;
  
  bmrVal.textContent = `${Math.round(bmr).toLocaleString()} kcal`;
  tdeeVal.textContent = `${Math.round(tdee).toLocaleString()} kcal`;

  // 4. Generate Health Insights text
  generateInsights(bmi, category, minIdealKg, maxIdealKg, bmr, tdee);

  // 5. Update Nomogram Chart position
  updateNomogramChart(state.heightCm, state.weightKg);
  
  // 6. Update Log Table view
  renderLogTable();
}

function generateInsights(bmi, category, minIdealKg, maxIdealKg, bmr, tdee) {
  const dispHeight = state.currentUnit === 'metric' ? `${Math.round(state.heightCm)} cm` : `${cmToFtIn(state.heightCm).ft}'${cmToFtIn(state.heightCm).in}"`;
  const dispWeight = state.currentUnit === 'metric' ? `${formatNumber(state.weightKg, 1)} kg` : `${formatNumber(state.weightLb, 1)} lbs`;
  const unitSuffix = state.currentUnit === 'metric' ? 'kg' : 'lbs';
  
  let mainTip = '';
  let alertVal = '';
  let bmrTdeeTip = '';
  
  if (category === 'Underweight') {
    alertVal = 'underweight';
    const gap = minIdealKg - state.weightKg;
    const dispGap = state.currentUnit === 'metric' ? gap : kgToLb(gap);
    mainTip = `Your body mass index is <strong>${formatNumber(bmi, 1)}</strong> (Underweight). To reach a normal weight, you need to gain approximately <strong>${formatNumber(dispGap, 1)} ${unitSuffix}</strong>.`;
    bmrTdeeTip = `To gain weight healthily, aim to eat at a surplus of 300-500 kcal, bringing your daily goal to <strong>${Math.round(tdee + 400).toLocaleString()} kcal/day</strong>.`;
  } else if (category === 'Normal') {
    alertVal = 'normal';
    mainTip = `Your body mass index is <strong>${formatNumber(bmi, 1)}</strong> (Normal). You are in a healthy weight range for your height. Focus on maintaining your current active lifestyle.`;
    bmrTdeeTip = `To maintain your weight, consume around your TDEE of <strong>${Math.round(tdee).toLocaleString()} kcal/day</strong>.`;
  } else if (category === 'Overweight') {
    alertVal = 'overweight';
    const gap = state.weightKg - maxIdealKg;
    const dispGap = state.currentUnit === 'metric' ? gap : kgToLb(gap);
    mainTip = `Your body mass index is <strong>${formatNumber(bmi, 1)}</strong> (Overweight). To reach a normal weight range, you need to lose approximately <strong>${formatNumber(dispGap, 1)} ${unitSuffix}</strong>.`;
    bmrTdeeTip = `To lose weight safely, target a daily calorie deficit of 500 kcal, aiming for <strong>${Math.round(tdee - 500).toLocaleString()} kcal/day</strong>.`;
  } else {
    alertVal = 'obese';
    const gap = state.weightKg - maxIdealKg;
    const dispGap = state.currentUnit === 'metric' ? gap : kgToLb(gap);
    mainTip = `Your body mass index is <strong>${formatNumber(bmi, 1)}</strong> (Obese). A weight reduction of <strong>${formatNumber(dispGap, 1)} ${unitSuffix}</strong> is recommended to return to a healthier weight range.`;
    bmrTdeeTip = `To lose fat and boost metabolic health, focus on a daily intake of <strong>${Math.round(tdee - 500).toLocaleString()} kcal/day</strong>.`;
  }

  // Weight goal tip
  let goalTip = '';
  if (state.targetWeight) {
    const diff = state.weightKg - state.targetWeight;
    const dispDiff = state.currentUnit === 'metric' ? Math.abs(diff) : Math.abs(kgToLb(diff));
    const targetDisp = state.currentUnit === 'metric' ? `${state.targetWeight} kg` : `${formatNumber(kgToLb(state.targetWeight), 1)} lbs`;
    
    if (diff > 0.1) {
      const weeks = Math.ceil((diff * 7700) / 3500);
      goalTip = `Target: <strong>${targetDisp}</strong>. You are <strong>${formatNumber(dispDiff, 1)} ${unitSuffix}</strong> above your goal. At a 500 kcal deficit, you can achieve this in about <strong>${Math.max(1, weeks)} weeks</strong>.`;
    } else if (diff < -0.1) {
      const weeks = Math.ceil((Math.abs(diff) * 7700) / 3500);
      goalTip = `Target: <strong>${targetDisp}</strong>. You are <strong>${formatNumber(dispDiff, 1)} ${unitSuffix}</strong> below your goal. At a 500 kcal surplus, you can achieve this in about <strong>${Math.max(1, weeks)} weeks</strong>.`;
    } else {
      goalTip = `Goal Achieved! You have successfully reached your weight target of <strong>${targetDisp}</strong>.`;
    }
  } else {
    goalTip = `Tip: Set a Weight Goal in the inputs panel to get timeline estimations.`;
  }

  // Generate Bullet points based on BMI category
  let nutritionBullets = [];
  let exerciseBullets = [];
  let videos = [];

  if (category === 'Underweight') {
    nutritionBullets = [
      "Eat at a caloric surplus: Aim for 300 - 500 kcal above your TDEE daily.",
      "Prioritize proteins: Consume 1.6 - 2.0g per kg of bodyweight for muscle gain.",
      "Eat nutrient-dense fats: Nuts, avocados, seeds, olive oil, and whole eggs.",
      "Increase meal frequency: Plan 5-6 smaller meals per day to manage fullness."
    ];
    exerciseBullets = [
      "Prioritize compound lifts (squats, bench, deadlifts) 3-4 days a week.",
      "Limit high-intensity cardio to conserve calories for muscle synthesis.",
      "Sleep 8+ hours nightly to facilitate optimal muscle recovery and growth."
    ];
    videos = [
      {
        title: "How to Gain Weight Fast & Healthy (Bulk Guide)",
        channel: "PictureFit",
        url: "https://www.youtube.com/watch?v=5_j1zVlQOsk",
        tag: "DIET TIPS"
      },
      {
        title: "How to Build Muscle (The Complete Beginner's Guide)",
        channel: "Jeremy Ethier",
        url: "https://www.youtube.com/watch?v=U9ENCv1pTGA",
        tag: "WORKOUT"
      }
    ];
  } else if (category === 'Normal') {
    nutritionBullets = [
      "Maintain balance: Consume calories close to your maintenance TDEE.",
      "Eat whole foods: Prioritize lean proteins, complex carbs, and fiber.",
      "Stay hydrated: Drink 2.5 - 3.5 liters of clean water daily.",
      "Follow the 80/20 rule: 80% clean whole food nutrition, 20% treats."
    ];
    exerciseBullets = [
      "Engage in 150 minutes of moderate aerobic cardiovascular exercise weekly.",
      "Incorporate resistance training 2-3 times a week to keep muscles active.",
      "Practice yoga or light stretching to maintain joint flexibility and mobility."
    ];
    videos = [
      {
        title: "How to Eat Healthy (Balanced Nutrition Guide)",
        channel: "PictureFit",
        url: "https://www.youtube.com/watch?v=Vl8dFfR2tmg",
        tag: "NUTRITION"
      },
      {
        title: "The Perfect Beginner Workout Routine",
        channel: "Jeremy Ethier",
        url: "https://www.youtube.com/watch?v=yev2k53l3Wc",
        tag: "FITNESS"
      }
    ];
  } else {
    // Overweight and Obese
    nutritionBullets = [
      "Eat in a calorie deficit: Consume 500 kcal below your TDEE daily.",
      "Focus on high-volume, low-calorie foods: Fill half your plate with vegetables.",
      "Increase lean proteins (chicken, fish, tofu) to protect muscle tissue.",
      "Zero liquid calories: Avoid sodas, alcohol, and sugary coffee drinks."
    ];
    exerciseBullets = [
      "Increase physical activity (NEAT): Aim for 8,000 - 10,000 steps daily.",
      "Do full body strength training 3 times/week to support metabolism.",
      "Add 2-3 sessions of moderate cardio or HIIT to increase fat burning."
    ];
    videos = [
      {
        title: "How to Eat to Lose Fat (Scientific Fat Loss Guide)",
        channel: "Jeremy Ethier",
        url: "https://www.youtube.com/watch?v=g9K3tG-mpxY",
        tag: "WEIGHT LOSS"
      },
      {
        title: "15 Min Daily Fat Burning Workout (No Equipment)",
        channel: "MadFit",
        url: "https://www.youtube.com/watch?v=gC_L9qAHVJ8",
        tag: "HOME WORKOUT"
      }
    ];
  }

  // HTML generation
  insightsText.innerHTML = `
    <div class="insights-dashboard">
      <!-- Top Overview Alert -->
      <div class="insight-alert val-${alertVal}">
        <div class="alert-icon">
          <i data-lucide="info"></i>
        </div>
        <div class="alert-text">
          <p>${mainTip} <strong>${bmrTdeeTip}</strong></p>
          <p style="margin-top: 0.25rem; font-size: 0.8rem; opacity: 0.85;">${goalTip}</p>
        </div>
      </div>

      <!-- 3-Column Recommendations Grid -->
      <div class="insights-grid">
        <!-- Nutrition Box -->
        <div class="insight-box nutrition-box">
          <div class="box-header">
            <i data-lucide="apple"></i>
            <h3>Nutrition Recommendations</h3>
          </div>
          <ul class="box-list">
            ${nutritionBullets.map(bullet => `<li>${bullet}</li>`).join('')}
          </ul>
        </div>

        <!-- Exercise Box -->
        <div class="insight-box exercise-box">
          <div class="box-header">
            <i data-lucide="dumbbell"></i>
            <h3>Exercise & Activity</h3>
          </div>
          <ul class="box-list">
            ${exerciseBullets.map(bullet => `<li>${bullet}</li>`).join('')}
          </ul>
        </div>

        <!-- Videos Recommendations Box -->
        <div class="insight-box videos-box">
          <div class="box-header">
            <i data-lucide="youtube"></i>
            <h3>Video Resources</h3>
          </div>
          <div class="videos-grid">
            ${videos.map((vid, idx) => `
              <a href="${vid.url}" target="_blank" class="video-card">
                <div class="video-thumbnail">
                  <div class="play-overlay">
                    <i data-lucide="play"></i>
                  </div>
                  <span class="video-tag">${vid.tag}</span>
                </div>
                <div class="video-info">
                  <h4 class="video-title">${vid.title}</h4>
                  <span class="video-channel">${vid.channel}</span>
                </div>
              </a>
            `).join('')}
          </div>
        </div>
      </div>
    </div>
  `;

  // Re-initialize Lucide icons inside this newly generated HTML
  lucide.createIcons();
}

// --- History Log Operations ---
function renderLogTable() {
  if (state.logs.length === 0) {
    historyBody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center text-muted py-4">No data logged yet. Save a calculation to start tracking.</td>
      </tr>
    `;
    return;
  }

  // Sort logs by date descending
  const sortedLogs = [...state.logs].sort((a, b) => new Date(b.date) - new Date(a.date));

  historyBody.innerHTML = sortedLogs.map(log => {
    const logDate = new Date(log.date).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });

    const isMetric = state.currentUnit === 'metric';
    
    // Convert logs dynamically to active unit
    const displayH = isMetric 
      ? `${Math.round(log.heightCm)} cm` 
      : `${cmToFtIn(log.heightCm).ft}'${cmToFtIn(log.heightCm).in}"`;
      
    const displayW = isMetric 
      ? `${formatNumber(log.weightKg, 1)} kg` 
      : `${formatNumber(kgToLb(log.weightKg), 1)} lbs`;

    const details = getBmiDetails(log.heightCm, log.weightKg);
    const badgeClass = `badge-${details.category.toLowerCase()}`;

    const notesText = log.notes || '-';
    const ageGenderText = `${log.age}y / ${log.gender === 'male' ? 'M' : 'F'}`;

    return `
      <tr data-id="${log.id}">
        <td>${logDate}</td>
        <td>${displayH}</td>
        <td><strong>${displayW}</strong></td>
        <td><strong>${formatNumber(details.bmi, 1)}</strong></td>
        <td><span class="table-badge ${badgeClass}">${details.category}</span></td>
        <td>${ageGenderText}</td>
        <td><span class="text-muted" title="${notesText}">${notesText}</span></td>
      </tr>
    `;
  }).join('');

  // Re-run Lucide icons replacement on new dynamically added elements
  lucide.createIcons();
}

window.deleteLogEntry = function(id) {
  if (confirm("Are you sure you want to delete this entry?")) {
    state.logs = state.logs.filter(log => log.id !== id);
    saveToStorage();
    updateDashboardUI();
    updateTrendChart();
  }
};

window.editLogEntry = function(id) {
  const log = state.logs.find(l => l.id === id);
  if (!log) return;

  state.editingLogId = log.id;
  state.gender = log.gender;
  state.heightCm = log.heightCm;
  state.weightKg = log.weightKg;
  state.age = log.age;
  state.activity = log.activity || 1.375;
  state.targetWeight = log.targetWeight || null;

  // Sync inputs
  const imperialH = cmToFtIn(state.heightCm);
  state.heightFt = imperialH.ft;
  state.heightIn = imperialH.in;
  state.weightLb = kgToLb(state.weightKg);

  // Set values on form fields
  // Radios
  for (let radio of genderRadios) {
    if (radio.value === state.gender) radio.checked = true;
  }
  
  heightCmSlider.value = Math.round(state.heightCm);
  heightCmNum.value = Math.round(state.heightCm);
  heightCmVal.textContent = `${Math.round(state.heightCm)} cm`;
  
  weightKgSlider.value = state.weightKg;
  weightKgNum.value = formatNumber(state.weightKg, 1);
  weightKgVal.textContent = `${formatNumber(state.weightKg, 1)} kg`;
  
  weightLbSlider.value = Math.round(state.weightLb);
  weightLbNum.value = formatNumber(state.weightLb, 1);
  weightLbVal.textContent = `${formatNumber(state.weightLb, 1)} lbs`;
  
  heightFtInput.value = state.heightFt;
  heightInInput.value = state.heightIn;

  ageInput.value = state.age;
  activitySelect.value = state.activity;
  
  if (state.targetWeight) {
    const dispTarget = state.currentUnit === 'metric' ? state.targetWeight : kgToLb(state.targetWeight);
    targetWeightInput.value = formatNumber(dispTarget, 1);
    targetWeightBadge.textContent = `${formatNumber(dispTarget, 1)} ${state.currentUnit === 'metric' ? 'kg' : 'lbs'}`;
    targetWeightBadge.classList.remove('badge-neutral');
  } else {
    targetWeightInput.value = '';
    targetWeightBadge.textContent = 'None';
    targetWeightBadge.classList.add('badge-neutral');
  }

  // Focus and scroll to calculation panel
  document.querySelector('.calculator-card').scrollIntoView({ behavior: 'smooth' });
  calculateBtn.innerHTML = `<i data-lucide="check"></i> Update Values`;
  saveLogBtn.innerHTML = `<i data-lucide="save"></i> Save Changes`;
  lucide.createIcons();
  
  updateDashboardUI();
};

function addOrUpdateLog() {
  const note = prompt(state.editingLogId ? "Update note for this log entry (optional):" : "Add note for this log entry (optional):");
  if (note === null) return; // user cancelled prompt entirely
  
  const bmiDetails = getBmiDetails(state.heightCm, state.weightKg);

  if (state.editingLogId) {
    // Update existing
    const logIndex = state.logs.findIndex(l => l.id === state.editingLogId);
    if (logIndex !== -1) {
      state.logs[logIndex].heightCm = state.heightCm;
      state.logs[logIndex].weightKg = state.weightKg;
      state.logs[logIndex].bmi = bmiDetails.bmi;
      state.logs[logIndex].category = bmiDetails.category;
      state.logs[logIndex].age = state.age;
      state.logs[logIndex].gender = state.gender;
      state.logs[logIndex].activity = state.activity;
      state.logs[logIndex].targetWeight = state.targetWeight;
      state.logs[logIndex].notes = note || state.logs[logIndex].notes;
    }
    state.editingLogId = null;
    calculateBtn.innerHTML = `<i data-lucide="arrow-right"></i> Calculate BMI`;
    saveLogBtn.innerHTML = `<i data-lucide="plus"></i> Save to Log`;
    lucide.createIcons();
  } else {
    // Add new
    const newLog = {
      id: Date.now().toString(36) + Math.random().toString(36).substr(2, 5),
      date: new Date().toISOString(),
      heightCm: state.heightCm,
      weightKg: state.weightKg,
      bmi: bmiDetails.bmi,
      category: bmiDetails.category,
      age: state.age,
      gender: state.gender,
      activity: state.activity,
      targetWeight: state.targetWeight,
      notes: note || ""
    };
    state.logs.push(newLog);
  }

  saveToStorage();
  updateDashboardUI();
  updateTrendChart();
}

// --- Chart.js Initializations & Updates ---

function initCharts() {
  // 1. Initialize Nomogram Chart
  const ctxNom = document.getElementById('nomogramChart').getContext('2d');
  nomogramChart = new Chart(ctxNom, {
    type: 'scatter',
    data: {
      datasets: [{
        label: 'Your Weight Position',
        data: [{ x: state.heightCm, y: state.weightKg }],
        backgroundColor: '#8b5cf6', // purple accent
        borderColor: '#ffffff',
        borderWidth: 2,
        pointRadius: 9,
        pointHoverRadius: 11,
        pointStyle: 'rectRot', // diamond style marker
        showLine: false
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 39, 0.95)',
          titleColor: '#ffffff',
          bodyColor: '#f3f4f6',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          padding: 12,
          displayColors: false,
          callbacks: {
            title: () => 'Your Coordinates',
            label: function(context) {
              const h = context.raw.x;
              const w = context.raw.y;
              const bmi = (w / ((h / 100) ** 2)).toFixed(1);
              
              const hFtIn = cmToFtIn(h);
              const wLbs = kgToLb(w);
              
              return [
                `Height: ${h} cm (${hFtIn.ft}'${hFtIn.in}")`,
                `Weight: ${w.toFixed(1)} kg (${wLbs.toFixed(1)} lbs)`,
                `BMI: ${bmi} (${getBmiDetails(h, w).category})`
              ];
            }
          }
        }
      },
      scales: {
        x: {
          type: 'linear',
          position: 'bottom',
          min: 130,
          max: 210,
          title: {
            display: true,
            text: 'Height (cm)',
            color: 'var(--text-secondary)',
            font: { family: 'Outfit', weight: 600, size: 12 }
          },
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { color: 'var(--text-secondary)' }
        },
        y: {
          type: 'linear',
          min: 30,
          max: 130,
          title: {
            display: true,
            text: 'Weight (kg)',
            color: 'var(--text-secondary)',
            font: { family: 'Outfit', weight: 600, size: 12 }
          },
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { color: 'var(--text-secondary)' }
        }
      }
    },
    plugins: [nomogramBmiPlugin]
  });

  // 2. Initialize Trend Chart
  const ctxTrend = document.getElementById('trendChart').getContext('2d');
  trendChart = new Chart(ctxTrend, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Weight',
          data: [],
          borderColor: '#8b5cf6',
          backgroundColor: 'rgba(139, 92, 246, 0.1)',
          fill: true,
          tension: 0.3,
          borderWidth: 3,
          pointBackgroundColor: '#8b5cf6',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 1.5,
          pointRadius: 5,
          yAxisID: 'y'
        },
        {
          label: 'BMI',
          data: [],
          borderColor: '#10b981',
          backgroundColor: 'transparent',
          borderWidth: 2.5,
          borderDash: [4, 4],
          pointRadius: 0,
          tension: 0.3,
          yAxisID: 'yBmi'
        },
        {
          label: 'Target Weight',
          data: [],
          borderColor: '#f59e0b',
          borderDash: [6, 6],
          borderWidth: 2,
          pointRadius: 0,
          fill: false,
          yAxisID: 'y'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          labels: {
            color: 'var(--text-secondary)',
            font: { family: 'Inter', weight: 600 }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 39, 0.95)',
          padding: 12,
          borderWidth: 1,
          borderColor: 'rgba(255,255,255,0.1)'
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.03)' },
          ticks: { color: 'var(--text-secondary)' }
        },
        y: {
          type: 'linear',
          position: 'left',
          title: {
            display: true,
            text: 'Weight',
            color: 'var(--text-secondary)',
            font: { family: 'Outfit', weight: 600 }
          },
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { color: 'var(--text-secondary)' }
        },
        yBmi: {
          type: 'linear',
          position: 'right',
          title: {
            display: true,
            text: 'BMI',
            color: 'var(--text-secondary)',
            font: { family: 'Outfit', weight: 600 }
          },
          grid: { drawOnChartArea: false },
          ticks: { color: 'var(--text-secondary)' }
        }
      }
    }
  });

  updateTrendChart();
}

function updateNomogramChart(heightCm, weightKg) {
  if (!nomogramChart) return;

  // Auto-expand scales if user lies outside bounds
  let minH = 130;
  let maxH = 210;
  let minW = 30;
  let maxW = 130;

  if (heightCm < minH + 5) minH = Math.max(80, Math.floor(heightCm - 10));
  if (heightCm > maxH - 5) maxH = Math.min(270, Math.ceil(heightCm + 10));
  if (weightKg < minW + 5) minW = Math.max(10, Math.floor(weightKg - 10));
  if (weightKg > maxW - 5) maxW = Math.min(350, Math.ceil(weightKg + 10));

  nomogramChart.options.scales.x.min = minH;
  nomogramChart.options.scales.x.max = maxH;
  nomogramChart.options.scales.y.min = minW;
  nomogramChart.options.scales.y.max = maxW;

  nomogramChart.data.datasets[0].data = [{ x: heightCm, y: weightKg }];
  
  // Theme styling updates for the chart
  const isLight = document.body.classList.contains('light-theme');
  const textColor = isLight ? '#4b5563' : '#9ca3af';
  const gridColor = isLight ? 'rgba(0,0,0,0.05)' : 'rgba(255,255,255,0.05)';
  
  nomogramChart.options.scales.x.ticks.color = textColor;
  nomogramChart.options.scales.x.title.color = textColor;
  nomogramChart.options.scales.x.grid.color = gridColor;
  nomogramChart.options.scales.y.ticks.color = textColor;
  nomogramChart.options.scales.y.title.color = textColor;
  nomogramChart.options.scales.y.grid.color = gridColor;
  nomogramChart.data.datasets[0].borderColor = isLight ? '#6366f1' : '#ffffff';
  nomogramChart.data.datasets[0].backgroundColor = isLight ? '#4f46e5' : '#8b5cf6';

  nomogramChart.update('none'); // Update without full animation for smoother responsiveness
}

function updateTrendChart() {
  if (!trendChart) return;

  const isMetric = state.currentUnit === 'metric';
  const unitText = isMetric ? 'kg' : 'lbs';

  if (state.logs.length === 0) {
    // Clear chart if no data
    trendChart.data.labels = [];
    trendChart.data.datasets[0].data = [];
    trendChart.data.datasets[1].data = [];
    trendChart.data.datasets[2].data = [];
    trendChart.update();
    return;
  }

  // Sort logs chronologically
  const chronologicalLogs = [...state.logs].sort((a, b) => new Date(a.date) - new Date(b.date));

  // Format Dates
  const labels = chronologicalLogs.map(log => {
    return new Date(log.date).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric'
    });
  });

  // Weights mapping
  const weights = chronologicalLogs.map(log => {
    return isMetric ? log.weightKg : kgToLb(log.weightKg);
  });

  // BMIs mapping
  const bmis = chronologicalLogs.map(log => {
    const details = getBmiDetails(log.heightCm, log.weightKg);
    return details.bmi;
  });

  // Target Weight mapping
  const targets = chronologicalLogs.map(() => {
    if (state.targetWeight) {
      return isMetric ? state.targetWeight : kgToLb(state.targetWeight);
    }
    return null;
  });

  trendChart.data.labels = labels;
  trendChart.data.datasets[0].data = weights;
  trendChart.data.datasets[0].label = `Weight (${unitText})`;
  trendChart.data.datasets[1].data = bmis;

  if (state.targetWeight) {
    trendChart.data.datasets[2].data = targets;
    trendChart.data.datasets[2].label = `Target (${unitText})`;
  } else {
    trendChart.data.datasets[2].data = [];
  }

  // Apply Theme adjustments
  const isLight = document.body.classList.contains('light-theme');
  const textColor = isLight ? '#4b5563' : '#9ca3af';
  const gridColor = isLight ? 'rgba(0,0,0,0.05)' : 'rgba(255,255,255,0.04)';
  
  trendChart.options.scales.x.ticks.color = textColor;
  trendChart.options.scales.x.grid.color = gridColor;
  trendChart.options.scales.y.ticks.color = textColor;
  trendChart.options.scales.y.title.color = textColor;
  trendChart.options.scales.y.title.text = `Weight (${unitText})`;
  trendChart.options.scales.y.grid.color = gridColor;
  trendChart.options.scales.yBmi.ticks.color = textColor;
  trendChart.options.scales.yBmi.title.color = textColor;
  
  trendChart.options.plugins.legend.labels.color = textColor;

  trendChart.update();
}

// --- Import / Export ---
function exportData() {
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(state.logs, null, 2));
  const dlAnchorElem = document.createElement('a');
  dlAnchorElem.setAttribute("href", dataStr);
  dlAnchorElem.setAttribute("download", `fitscale-bmi-logs-${new Date().toISOString().split('T')[0]}.json`);
  dlAnchorElem.click();
}

function importData(e) {
  const fileReader = new FileReader();
  fileReader.onload = function(event) {
    try {
      const parsed = JSON.parse(event.target.result);
      if (Array.isArray(parsed)) {
        // Simple validation check
        const isValid = parsed.every(item => item.heightCm && item.weightKg && item.date);
        if (isValid) {
          state.logs = parsed;
          saveToStorage();
          updateDashboardUI();
          updateTrendChart();
          alert("Logs imported successfully!");
        } else {
          alert("Invalid file format. Make sure the JSON file contains appropriate height, weight, and date properties.");
        }
      } else {
        alert("Invalid file format. Must be a JSON array.");
      }
    } catch (err) {
      alert("Error parsing file. Make sure it is a valid JSON document.");
    }
  };
  if (e.target.files[0]) {
    fileReader.readAsText(e.target.files[0]);
  }
}

// --- Sample Data Injection ---
function injectSampleData() {
  const now = new Date();
  const sampleLogs = [];
  
  // Create 8 records over the past 8 weeks, showing weight loss progress
  let w = 84.5; // Starting weight
  let h = 175;  // Height
  let a = 28;
  let g = 'male';
  let act = 1.375;
  let target = 72;

  const notes = [
    "Starting weight loss journey, feeling determined.",
    "First week check-in. Cut down on carbs.",
    "Gym workout twice this week. Energy levels up.",
    "Consistent calorie count, lost some water weight.",
    "Had a cheat meal this weekend, weight fluctuated slightly.",
    "Back on track. Doing more morning walks.",
    "Nearing normal BMI range, feeling much lighter!",
    "Official check-in. Weight continues to go down."
  ];

  for (let i = 7; i >= 0; i--) {
    const entryDate = new Date(now.getTime() - i * 7 * 24 * 60 * 60 * 1000);
    // Add random slight fluctuations but general downwards trend
    if (i === 3) {
      w = w + 0.3; // Slight fluctuation
    } else {
      w = w - (0.8 + Math.random() * 0.6); // Weight loss
    }

    const bmiDetails = getBmiDetails(h, w);

    sampleLogs.push({
      id: `sample-${i}`,
      date: entryDate.toISOString(),
      heightCm: h,
      weightKg: parseFloat(w.toFixed(1)),
      bmi: bmiDetails.bmi,
      category: bmiDetails.category,
      age: a,
      gender: g,
      activity: act,
      targetWeight: target,
      notes: notes[7 - i]
    });
  }

  state.logs = sampleLogs;
  state.targetWeight = target;
  state.heightCm = h;
  state.weightKg = parseFloat(w.toFixed(1));
  state.gender = g;
  state.age = a;
  state.activity = act;

  // Sync controls inputs
  heightCmSlider.value = h;
  heightCmNum.value = h;
  heightCmVal.textContent = `${h} cm`;

  weightKgSlider.value = parseFloat(w.toFixed(1));
  weightKgNum.value = parseFloat(w.toFixed(1));
  weightKgVal.textContent = `${parseFloat(w.toFixed(1))} kg`;

  const imperialH = cmToFtIn(h);
  heightFtInput.value = imperialH.ft;
  heightInInput.value = imperialH.in;

  const lb = kgToLb(w);
  weightLbSlider.value = Math.round(lb);
  weightLbNum.value = formatNumber(lb, 1);
  weightLbVal.textContent = `${formatNumber(lb, 1)} lbs`;

  ageInput.value = a;
  activitySelect.value = act;
  
  const dispTarget = state.currentUnit === 'metric' ? target : kgToLb(target);
  targetWeightInput.value = formatNumber(dispTarget, 1);
  targetWeightBadge.textContent = `${formatNumber(dispTarget, 1)} ${state.currentUnit === 'metric' ? 'kg' : 'lbs'}`;
  targetWeightBadge.classList.remove('badge-neutral');

  saveToStorage();
  updateDashboardUI();
  updateTrendChart();
}

// --- Event Listeners Registration ---

function registerEventListeners() {
  // Theme Toggle
  themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark-theme');
    document.body.classList.toggle('light-theme');
    
    // Save theme preference
    const activeTheme = document.body.classList.contains('light-theme') ? 'light' : 'dark';
    localStorage.setItem('fitscale_theme', activeTheme);
    
    // Update charts color systems
    updateNomogramChart(state.heightCm, state.weightKg);
    updateTrendChart();
  });

  // Unit Tabs switching
  unitTabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
      const unit = e.currentTarget.dataset.unit;
      if (unit === state.currentUnit) return;
      state.currentUnit = unit;
      
      updateUnitTabUI();
      updateDashboardUI();
      updateTrendChart();
    });
  });

  // Height Slider Sync
  heightCmSlider.addEventListener('input', () => syncHeightInputs('slider'));
  heightCmNum.addEventListener('input', () => syncHeightInputs('number'));
  heightFtInput.addEventListener('input', () => syncHeightInputs('imperial'));
  heightInInput.addEventListener('input', () => syncHeightInputs('imperial'));

  // Weight Slider Sync
  weightKgSlider.addEventListener('input', () => syncWeightInputs('slider-metric'));
  weightKgNum.addEventListener('input', () => syncWeightInputs('number-metric'));
  weightLbSlider.addEventListener('input', () => syncWeightInputs('slider-imperial'));
  weightLbNum.addEventListener('input', () => syncWeightInputs('number-imperial'));

  // Age change
  ageInput.addEventListener('input', () => {
    const age = parseInt(ageInput.value);
    if (!isNaN(age)) state.age = age;
  });

  // Activity change
  activitySelect.addEventListener('change', () => {
    state.activity = parseFloat(activitySelect.value);
  });

  // Target Weight change
  targetWeightInput.addEventListener('input', () => {
    const val = parseFloat(targetWeightInput.value);
    if (isNaN(val) || val <= 0) {
      state.targetWeight = null;
      targetWeightBadge.textContent = 'None';
      targetWeightBadge.classList.add('badge-neutral');
    } else {
      if (state.currentUnit === 'metric') {
        state.targetWeight = val;
        targetWeightBadge.textContent = `${formatNumber(val, 1)} kg`;
      } else {
        state.targetWeight = lbToKg(val);
        targetWeightBadge.textContent = `${formatNumber(val, 1)} lbs`;
      }
      targetWeightBadge.classList.remove('badge-neutral');
    }
  });

  // Target weight clear button
  clearTargetBtn.addEventListener('click', () => {
    state.targetWeight = null;
    targetWeightInput.value = '';
    targetWeightBadge.textContent = 'None';
    targetWeightBadge.classList.add('badge-neutral');
    updateDashboardUI();
    updateTrendChart();
  });

  // Gender change
  genderRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
      state.gender = e.target.value;
    });
  });

  // Calculate submit
  bmiForm.addEventListener('submit', (e) => {
    e.preventDefault();
    updateDashboardUI();
  });

  // Save to Log
  saveLogBtn.addEventListener('click', () => {
    addOrUpdateLog();
  });

  // Chart View Tabs switching
  chartTabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
      const selectedChart = e.currentTarget.dataset.chart;
      
      chartTabs.forEach(t => t.classList.remove('active'));
      e.currentTarget.classList.add('active');

      if (selectedChart === 'nomogram') {
        nomogramContainer.classList.remove('hidden');
        trendContainer.classList.add('hidden');
        nomogramChart.resize();
      } else {
        nomogramContainer.classList.add('hidden');
        trendContainer.classList.remove('hidden');
        trendChart.resize();
      }
    });
  });

  // Export / Import
  exportJsonBtn.addEventListener('click', exportData);
  importTriggerBtn.addEventListener('click', () => importFile.click());
  importFile.addEventListener('change', importData);
  
  // Clear all
  clearAllBtn.addEventListener('click', () => {
    if (confirm("Are you sure you want to clear all history logs? This cannot be undone.")) {
      state.logs = [];
      saveToStorage();
      updateDashboardUI();
      updateTrendChart();
    }
  });

  // Load sample data button
  loadSampleBtn.addEventListener('click', injectSampleData);
}

// --- App Initialization ---

document.addEventListener('DOMContentLoaded', () => {
  // Load Lucide Icons
  lucide.createIcons();

  // Load state and themes
  loadFromStorage();
  
  // Apply theme from localStorage if saved
  const savedTheme = localStorage.getItem('fitscale_theme');
  if (savedTheme === 'light') {
    document.body.classList.remove('dark-theme');
    document.body.classList.add('light-theme');
  }

  // Set initial UI states from state object
  updateUnitTabUI();
  
  // Sync slider label badges
  heightCmVal.textContent = `${state.heightCm} cm`;
  heightCmSlider.value = state.heightCm;
  heightCmNum.value = state.heightCm;

  weightKgVal.textContent = `${formatNumber(state.weightKg, 1)} kg`;
  weightKgSlider.value = state.weightKg;
  weightKgNum.value = formatNumber(state.weightKg, 1);

  const lb = kgToLb(state.weightKg);
  weightLbVal.textContent = `${formatNumber(lb, 1)} lbs`;
  weightLbSlider.value = Math.round(lb);
  weightLbNum.value = formatNumber(lb, 1);

  ageInput.value = state.age;
  activitySelect.value = state.activity;
  
  // Apply values to radios
  for (let radio of genderRadios) {
    if (radio.value === state.gender) radio.checked = true;
  }

  // Register event listeners
  registerEventListeners();

  // Initialize charts and dashboard UI rendering
  initCharts();
  updateDashboardUI();
});
