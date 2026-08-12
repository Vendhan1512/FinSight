# FinSight Leakage Prevention Rules

Look-Ahead Bias is the single greatest threat to a quantitative trading model. It occurs when a machine learning model is trained using data that would not have actually been known to a trader at that specific point in time. 

The FinSight `LeakageValidator` is a mathematical firewall. It strictly enforces the following rules:

## Rule 1: The Availability Law
$$ Availability\_Time \le Prediction\_Time $$

**Explanation:** An observation's timestamp (what the data describes) is irrelevant for prediction. The only timestamp that matters is when the data became *publicly available*.

**Example Violation:** 
*   **Observation:** Q1 Earnings (Jan 1 - Mar 31)
*   **Availability:** 10-Q Filed on May 10th.
*   **Leakage:** Assigning the Q1 Earnings to a prediction row for April 5th.
*   **Validator Action:** FATAL. The Validator will crash if the feature's availability column is strictly greater than the prediction column.

## Rule 2: The Macroeconomic Vintage Law (ALFRED)
$$ Realtime\_Start \le Prediction\_Time $$

**Explanation:** Macroeconomic numbers are heavily revised months after they are released. 

**Example Violation:**
*   **Observation:** January CPI.
*   **Availability 1 (Advance):** Released Feb 10th (Value = 290).
*   **Availability 2 (Revised):** Released Mar 10th (Value = 295).
*   **Leakage:** Using the revised 295 value to make a prediction on Feb 20th.
*   **Validator Action:** FATAL. The `PointInTimeJoiner` physically prevents this using a strictly backward `merge_asof` on the `realtime_start` column.

## Rule 3: The Rolling Window Law
**Explanation:** When calculating rolling statistics (like a 20-day moving average), the window must strictly look backwards (`min_periods=N`, trailing).

**Example Violation:**
*   Using a *centered* moving average, which looks 10 days into the past and 10 days into the future.
*   **Validator Action:** The Technical and Volume engines explicitly enforce trailing `.rolling()` calculations without shifting the target.

## Rule 4: The Unshifted Target Law
**Explanation:** The feature row at time `T` must predict the return at time `T+1`. 

**Example Violation:**
*   Accidentally calculating today's return and feeding it as a feature to predict today's return. 

## Fatal Actions
The `LeakageValidator` is designed to be ruthless. It does not attempt to impute, forward-fill, or silently fix leaking rows. If a single row out of a million violates the Availability Law, the pipeline will crash with a `LeakageDetectedError`.
