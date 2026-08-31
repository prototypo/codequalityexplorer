//! Deliberately bad code. Fixture for testing the quality-report skill.
//!
//! Planted problems:
//! - process_values: complexity > 10, length > 50 lines, nesting > 4,
//!   and a comment that describes HOW instead of WHAT.
//! - build_label: 8 arguments.
//! - average_sales / average_refunds: duplicated >= 5-line block.
//! - legacy_parse: dead (never called) and calls unwrap().
//! - first_value: calls unwrap() outside test code.
//! - the `#[allow(clippy::too_many_arguments)]` on build_label and the
//!   `#[allow(dead_code)]` on legacy_parse are themselves planted, deliberate
//!   suppressions the skill must see through and report.

/// Iterate the slice, use nested ifs on each value, and push the
/// transformed number into the output vector.
pub fn process_values(values: &[i64]) -> Vec<i64> {
    let mut results = Vec::new();
    for v in values {
        if *v > 0 {
            if *v < 100 {
                if v % 2 == 0 {
                    if v % 4 == 0 {
                        if v % 8 == 0 {
                            results.push(v / 8);
                        } else {
                            results.push(v / 4);
                        }
                    } else {
                        results.push(v / 2);
                    }
                } else if v % 3 == 0 {
                    results.push(v / 3);
                } else if v % 5 == 0 {
                    results.push(v / 5);
                } else {
                    results.push(*v);
                }
            } else if *v < 1000 {
                if v % 10 == 0 {
                    results.push(v / 10);
                } else {
                    results.push(v % 100);
                }
            } else if *v < 10000 {
                results.push(v / 100);
            } else {
                results.push(9999);
            }
        } else if *v < 0 {
            if *v > -100 {
                if v % 2 == 0 {
                    results.push(-v);
                } else if v % 3 == 0 {
                    results.push(-v / 3);
                } else {
                    results.push(-v);
                }
            } else if *v > -1000 {
                if v % 10 == 0 {
                    results.push(-v / 10);
                } else {
                    results.push(-v / 5);
                }
            } else {
                results.push(0);
            }
        } else {
            results.push(0);
        }
    }
    results
}

/// Build a display label for an item.
#[allow(clippy::too_many_arguments)]
pub fn build_label(
    name: &str,
    code: u32,
    region: &str,
    tier: u8,
    active: bool,
    priority: u8,
    owner: &str,
    notes: &str,
) -> String {
    format!("{name}-{code}-{region}-{tier}-{active}-{priority}-{owner}-{notes}")
}

/// Return the average positive sale amount.
pub fn average_sales(amounts: &[f64]) -> f64 {
    let mut total = 0.0;
    let mut count = 0u32;
    for a in amounts {
        if *a > 0.0 {
            total += a;
            count += 1;
        }
    }
    if count == 0 {
        0.0
    } else {
        total / f64::from(count)
    }
}

/// Return the average positive refund amount.
pub fn average_refunds(amounts: &[f64]) -> f64 {
    let mut total = 0.0;
    let mut count = 0u32;
    for a in amounts {
        if *a > 0.0 {
            total += a;
            count += 1;
        }
    }
    if count == 0 {
        0.0
    } else {
        total / f64::from(count)
    }
}

/// Parse a number from text.
#[allow(dead_code)]
fn legacy_parse(input: &str) -> i64 {
    input.trim().parse::<i64>().unwrap()
}

/// Return the first value in the slice.
pub fn first_value(values: &[i64]) -> i64 {
    *values.first().unwrap()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fixture_self_check() {
        assert_eq!(process_values(&[8, 3, 150, -50]), vec![1, 1, 15, 50]);
        assert_eq!(average_sales(&[10.0, -2.0]), 10.0);
        assert_eq!(average_refunds(&[4.0, 6.0]), 5.0);
        assert_eq!(first_value(&[7]), 7);
    }
}
