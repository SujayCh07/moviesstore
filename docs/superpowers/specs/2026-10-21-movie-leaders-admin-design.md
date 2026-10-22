# Movie Leaders Django Admin Design

## Goal

Provide a reproducible, staff-only Django admin report showing the movie or
movies with the most purchased copies and the movie or movies with the most
reviews, including the count for each category.

## Current system

- `movies.Movie` is the catalog record.
- `cart.Order` belongs to a user. `cart.Item` links an order to a movie and
  stores its purchased quantity.
- `movies.Review` links a movie to a user. `movies.Rating` is a separate
  one-per-user-per-movie score and is not a review.
- Checkout creates `Order` and `Item` records. Review submission creates a
  `Review` record.
- Django admin already registers movies, reviews, orders, and items, allowing
  staff to enter reproducible sample data.
- Story 5 code was added in commit `9289951` and removed in `2b982d2`; the
  `MovieLeaders` proxy migration remains, while the model, admin view, template,
  and tests are absent from the current tree.

## Proposed behavior

Add a `MovieLeaders` proxy model on `Movie`, registered in Django admin as a
read-only report. Its changelist displays two independent sections:

1. **Most purchased:** sum `Item.quantity` per movie across all orders. This
   measures purchased copies, not order rows or item rows.
2. **Most reviewed:** count `Review` rows per movie. Ratings do not count.
   Flagged reviews remain included, matching the existing Top Reviewer
   aggregation and the prior Story 5 implementation.

Each section lists all movies tied for its maximum, with the corresponding
count. A category with no qualifying records displays its own empty-state
message. The report recomputes from the source records on each request; it does
not persist aggregate counts. The proxy reuses the `Movie` table and does not
create a new table.

## End-to-end flow

1. A staff member signs into Django admin.
2. Staff create or select `Movie` records, then enter purchase data through
   `Order` and `Item` or review data through `Review`.
3. Staff open the **Movie Leaders** entry in the Movies admin section.
4. The custom admin changelist queries `Item` quantities and `Review` rows,
   independently aggregates each metric by movie, finds each maximum, and
   renders all leaders and counts in the report template.
5. Refreshing the page reflects newly created, edited, or deleted source rows.

The normal checkout and review flows produce the same source records. Django's
admin staff permission gate protects the report; there is no public URL, API,
or external service in this feature.

## Failure and edge cases

- No purchase rows: show the purchase empty state and no purchase leaders.
- No review rows: show the review empty state and no review leaders.
- Tied maximum: include every movie sharing that maximum, ordered by movie name
  and primary key for stable display.
- Same movie leads both metrics: show it in both independent sections.
- Different movies lead the metrics: show the correct leader in each section.
- Multiple order or item rows for a movie: sum all item quantities.
- Ratings exist without reviews: they do not affect review totals.
- Non-staff user requests the admin report: Django admin redirects to login or
  denies access according to the normal admin authentication flow.

## Reproduction and acceptance checks

Use Django admin to create two movies. Create `Item` rows linked through orders
with quantities `2`, `1`, and `4` for one movie; its purchase count should be
`7`. Add reviews and ratings independently, then open or refresh Movie Leaders
to check:

- one movie can lead both sections;
- different movies can lead purchases and reviews;
- tied movies all appear in each relevant section;
- empty purchase and review sections have separate messages;
- adding or removing source records changes the next report response;
- ratings alone do not change review counts; and
- a non-staff user cannot view the report.

Focused Django tests should cover these cases plus admin index discoverability.
The repository's Python interpreter currently cannot import Django, so the
available environment must be identified before running those tests.

## Implementation scope

Restore the model, admin registration and aggregate report, report template,
and focused tests, following the existing Top Reviewer, Top Buyer, and Purchase
Rankings patterns. Reconcile the model definition with the already-present
proxy migration. Do not add a public page, new database table, cache, or
external dependency.
