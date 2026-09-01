/**
 * Deliberately bad code. Fixture for testing the quality-report skill.
 *
 * Planted problems:
 * - processData: complexity > 10, length > 50 lines, nesting > 4, and a
 *   comment that describes HOW instead of WHAT.
 * - buildReport: 7 arguments.
 * - summarizeSales / summarizeRefunds: duplicated >= 5-line block.
 * - legacyExport: dead (never called), empty catch, an unused variable, and
 *   no comment of its own.
 */

// Loop through the items, use nested ifs to inspect each field, and push the
// transformed value onto the results array.
function processData(data) {
  const results = [];
  for (const item of data) {
    if (item !== null && item !== undefined) {
      if (Array.isArray(item)) {
        if (item.length > 10) {
          results.push(item.length);
        } else if (item.length > 5) {
          results.push(5);
        } else {
          results.push(0);
        }
      } else if (typeof item === 'object') {
        if ('value' in item) {
          if (item.value > 0) {
            if (item.value < 100) {
              results.push(item.value * 2);
            } else {
              results.push(100);
            }
          } else {
            results.push(0);
          }
        } else if ('name' in item) {
          if (item.name) {
            results.push(item.name.length);
          } else {
            results.push(-1);
          }
        } else {
          results.push(null);
        }
      } else if (typeof item === 'string') {
        if (item.startsWith('A')) {
          results.push(1);
        } else if (item.startsWith('B')) {
          results.push(2);
        } else if (item.startsWith('C')) {
          results.push(3);
        } else {
          results.push(0);
        }
      } else if (typeof item === 'number') {
        if (item % 2 === 0) {
          results.push(item / 2);
        } else {
          results.push(item * 3 + 1);
        }
      } else {
        results.push(null);
      }
    }
  }
  return results;
}

/** Build a report object from its parts. */
function buildReport(name, date, author, title, status, priority, category) {
  return { name, date, author, title, status, priority, category };
}

// Return the average positive sale amount.
const summarizeSales = (records) => {
  let total = 0;
  let count = 0;
  for (const record of records) {
    if (record.amount > 0) {
      total += record.amount;
      count += 1;
    }
  }
  return count ? total / count : 0;
};

// Return the average positive refund amount.
const summarizeRefunds = (records) => {
  let total = 0;
  let count = 0;
  for (const record of records) {
    if (record.amount > 0) {
      total += record.amount;
      count += 1;
    }
  }
  return count ? total / count : 0;
};

function legacyExport(records) {
  const unusedTotal = 0;
  try {
    return records.map((record) => String(record));
  } catch (err) {
  }
  return [];
}

export { processData, buildReport, summarizeSales, summarizeRefunds };
