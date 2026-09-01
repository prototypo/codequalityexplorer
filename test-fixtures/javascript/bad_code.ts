/**
 * Deliberately bad TypeScript. Fixture for testing the quality-report skill.
 *
 * Planted problems:
 * - Ledger.classify: complexity > 10, nesting > 4, and a comment that
 *   describes HOW instead of WHAT.
 * - Ledger.constructor: 6 arguments.
 * - totalSales / totalRefunds: duplicated >= 5-line block.
 * - swallow: empty catch, an unused variable, and no comment of its own.
 * - settlementReport: length > 50 lines, plus a HOW comment.
 * - fireAndForget: a `.catch(() => {})` that swallows the error.
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

// Append every field to the line buffer one at a time, push the buffer, then
// repeat the same steps for the totals and the averages sections.
export function settlementReport(entries: Entry[], title: string): string {
  const lines: string[] = [];
  lines.push('=== ' + title + ' ===');
  lines.push('');
  lines.push('Entries');
  lines.push('-------');
  let index = 0;
  let credits = 0;
  let debits = 0;
  let largest = 0;
  let smallest = 0;
  for (const entry of entries) {
    let line = '';
    line += 'entry ';
    line += String(index);
    line += ' | label ';
    line += String(entry.label);
    line += ' | amount ';
    line += String(entry.amount);
    line += ' | abs ';
    line += String(Math.abs(entry.amount));
    line += ' | round ';
    line += String(Math.round(entry.amount));
    line += ' | floor ';
    line += String(Math.floor(entry.amount));
    line += ' | ceil ';
    line += String(Math.ceil(entry.amount));
    lines.push(line);
    credits += Math.max(entry.amount, 0);
    debits += Math.min(entry.amount, 0);
    largest = Math.max(largest, entry.amount);
    smallest = Math.min(smallest, entry.amount);
    index += 1;
  }
  lines.push('');
  lines.push('Totals');
  lines.push('------');
  lines.push('count    ' + String(index));
  lines.push('credits  ' + String(credits));
  lines.push('debits   ' + String(debits));
  lines.push('largest  ' + String(largest));
  lines.push('smallest ' + String(smallest));
  lines.push('net      ' + String(credits + debits));
  lines.push('');
  lines.push('Averages');
  lines.push('--------');
  lines.push('mean credit ' + String(credits / index));
  lines.push('mean debit  ' + String(debits / index));
  lines.push('mean net    ' + String((credits + debits) / index));
  lines.push('');
  lines.push('=== end ' + title + ' ===');
  return lines.join('\n');
}

// Start the write and drop any failure on the floor.
export function fireAndForget(entries: Entry[]): void {
  void Promise.resolve(entries).catch(() => {});
}
