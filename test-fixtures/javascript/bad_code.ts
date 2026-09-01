/**
 * Deliberately bad TypeScript. Fixture for testing the quality-report skill.
 *
 * Planted problems:
 * - Ledger.classify: complexity > 10, nesting > 4, and a comment that
 *   describes HOW instead of WHAT.
 * - Ledger.constructor: 6 arguments.
 * - totalSales / totalRefunds: duplicated >= 5-line block.
 * - swallow: empty catch, an unused variable, and no comment of its own.
 */

export interface Entry {
  amount: number;
  label?: string;
}

export class Ledger {
  // Assign each constructor argument to an instance field one at a time.
  constructor(
    public name: string,
    public owner: string,
    public currency: string,
    public opened: string,
    public closed: string,
    public region: string,
  ) {}

  // Walk the entry through nested ifs on amount and label, returning the
  // first bucket name that matches.
  classify(entry: Entry): string {
    if (entry.amount > 0) {
      if (entry.label) {
        if (entry.label.length > 3) {
          if (entry.label.startsWith('x')) {
            if (entry.amount > 100) {
              return 'big-x';
            }
            return 'x';
          }
          return 'long';
        }
        return 'short';
      }
      return entry.amount > 50 ? 'large' : 'small';
    }
    if (entry.amount < 0) {
      return entry.label ?? 'refund';
    }
    if (Number.isNaN(entry.amount) || entry.label === undefined) {
      return 'unknown';
    }
    return 'zero';
  }
}

/** Return the average positive sale amount. */
export function totalSales(entries: Entry[]): number {
  let total = 0;
  let count = 0;
  for (const entry of entries) {
    if (entry.amount > 0) {
      total += entry.amount;
      count += 1;
    }
  }
  return count ? total / count : 0;
}

/** Return the average positive refund amount. */
export function totalRefunds(entries: Entry[]): number {
  let total = 0;
  let count = 0;
  for (const entry of entries) {
    if (entry.amount > 0) {
      total += entry.amount;
      count += 1;
    }
  }
  return count ? total / count : 0;
}

export function swallow(entries: Entry[]): string[] {
  const unusedTotal = 0;
  try {
    return entries.map((entry) => String(entry.amount));
  } catch (err) {
  }
  return [];
}
