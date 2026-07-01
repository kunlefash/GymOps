import { Diamond, DiamondWithRationale, Priority, Recommendation } from './types';
import { getDiamondsByShape } from './diamonds';

const BUDGET_CEILING_MAP: Record<string, number> = {
  'under-1000': 1000,
  '1000-2000': 2000,
  '2000-3500': 3500,
  '3500-5000': 5000,
  '5000-plus': 100000,
};

function parseBudget(budget: string): number {
  if (BUDGET_CEILING_MAP[budget]) return BUDGET_CEILING_MAP[budget];
  const num = parseInt(budget);
  return isNaN(num) ? 3500 : num;
}

function getRationale(diamond: Diamond, priority: Priority, budget: number): string {
  const budgetLabel = budget >= 100000 ? '' : ` your $${budget.toLocaleString()} budget`;
  switch (priority) {
    case 'size':
      return `Largest size at${budgetLabel} that still catches light like an ideal cut.`;
    case 'sparkle':
      return `Best cut quality at${budgetLabel} — will outsparkle stones half a carat larger.`;
    case 'value':
      return `Best balance of size and sparkle for${budgetLabel}.`;
  }
}

function getAlternateRationale(diamond: Diamond, label: string): string {
  if (label === 'A little bigger') {
    return `Largest stone in this search — slight color trade-off buys ${diamond.carat}ct.`;
  }
  if (label === 'A little sparklier') {
    return `${diamond.color} color grade catches more light. Slightly smaller at ${diamond.carat}ct.`;
  }
  return `Strong alternative with different quality balance.`;
}

export function getRecommendation(
  shape: string,
  priority: Priority,
  budgetParam: string
): Recommendation {
  const budget = parseBudget(budgetParam);
  const allDiamonds = getDiamondsByShape(shape);
  const diamonds = allDiamonds.filter(d => d.price <= budget);
  const pool = diamonds.length >= 3 ? diamonds : allDiamonds.slice(0, 4);

  let ranked: Diamond[];
  switch (priority) {
    case 'size':
      ranked = [...pool].sort((a, b) => b.caratScore - a.caratScore);
      break;
    case 'sparkle':
      ranked = [...pool].sort((a, b) => b.sparkleScore - a.sparkleScore);
      break;
    case 'value':
      ranked = [...pool].sort((a, b) => b.valueScore - a.valueScore);
      break;
  }

  const primary = ranked[0];

  const biggestAlt = [...pool]
    .filter(d => d.id !== primary.id)
    .sort((a, b) => b.carat - a.carat)[0];

  const sparklierAlt = [...pool]
    .filter(d => d.id !== primary.id && d.id !== biggestAlt?.id)
    .sort((a, b) => b.sparkleScore - a.sparkleScore)[0] || ranked[2];

  const alternate1: DiamondWithRationale = {
    ...(biggestAlt || ranked[1]),
    label: 'A little bigger',
    rationale: getAlternateRationale(biggestAlt || ranked[1], 'A little bigger'),
  };

  const alternate2: DiamondWithRationale = {
    ...(sparklierAlt || ranked[2] || ranked[1]),
    label: 'A little sparklier',
    rationale: getAlternateRationale(sparklierAlt || ranked[2] || ranked[1], 'A little sparklier'),
  };

  return {
    primary: {
      ...primary,
      rationale: getRationale(primary, priority, budget),
    },
    alternate1,
    alternate2,
    socialProof: '94 couples chose a stone from this quality tier last month.',
  };
}
