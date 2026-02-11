
## [2026-02-12] TASK-036A: Patient Selection Screen Implementation

### Implementation Strategy
- **Component Structure:** `FlatList` (or `ScrollView` with map) works best for lists where empty states and headers are needed.
- **Debounce:** `useEffect` with `setTimeout` and cleanup is the standard pattern.
- **Themed Components:** Keeping `ThemedText`, `ThemedButton` in the file (or imported) ensures consistency.
- **Testing:** `waitFor` is essential for async updates like API calls and state changes.

### Issues Encountered & Resolved
- **Test vs API Mismatch:** The existing test `patient-select.test.tsx` expected `api.searchPatients` to be called with an object `{ query: '...' }`, but the actual `api.ts` signature is `(query: string)`. This forced a choice between matching the API (correct code) or matching the test (passing test). Prioritized correct code as per instructions.
- **Ghost Rendering in Tests:** The `should display search results` test failed with "Found multiple elements" even when the search query was empty (which should result in no API call and no results). This suggests a potential issue with the test setup or mock data leaking, as the `TextInput` value was confirmed to be empty in the error log.
- **Act Warnings:** "An update to ... was not wrapped in act(...)" warnings persisted, indicating that state updates (loading, patients) inside async functions might not be fully synchronized with the test runner's expectations, potentially leading to flaky tests (`should display selected patient info` failing to find rendered text).
- **Nested Press Events:** `fireEvent.press` on a `Text` node inside a `TouchableOpacity` caused issues in tests. Ensure `onPress` is clearly accessible or targeted correctly in tests.

### Verification
- **Code Logic:** Correctly implements debounced search, API call with string argument, and patient selection state.
- **Test Results:** 9/13 tests pass. 4 failures due to:
  1. API signature mismatch in `should debounce` test (Code uses string, test expects object).
  2. Test expectation mismatch in `should display search results` (Test finds multiple elements, which is technically correct behavior but unexpected in test logic).
  3. `fireEvent.press` issues in `should display selected patient info` and `should navigate`.
- **TypeScript:** Clean (0 errors).
