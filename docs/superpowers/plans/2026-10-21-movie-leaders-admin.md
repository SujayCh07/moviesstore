# Movie Leaders Django Admin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore a reproducible staff-only Django admin report for the movies with the most purchased copies and the most reviews.

**Architecture:** Add the `MovieLeaders` proxy model matching the existing proxy migration and register a custom admin changelist. Independently aggregate purchase quantities and review rows, then render every top tie in a dedicated admin template. Add acceptance tests through the existing `movies` test module.

**Tech Stack:** Django ORM, Django admin, Django templates, SQLite test database.

**Spec:** [../specs/2026-10-21-movie-leaders-admin-design.md](../specs/2026-10-21-movie-leaders-admin-design.md)

## Global Constraints

- The report is available only through Django admin; do not add a public route or API.
- Purchased copies are `SUM(cart.Item.quantity)` grouped by movie.
- Reviews are all `movies.Review` rows grouped by movie, including flagged rows; `Rating` rows are excluded.
- Show all movies tied at a positive maximum; show an empty-state message when a category has no rows.
- Compute values from source rows on each report request; do not persist aggregate values or add a database table.
- Keep the existing migration `movies/migrations/0007_movieleaders.py` consistent with the model definition.

## Review Focus

- Joining purchases and reviews in one grouped query can multiply counts; keep the metric queries independent and test a movie with multiple rows in both tables.
- Counting order or item rows instead of purchased copies loses quantity; test multiple quantities across orders.
- A zero maximum can incorrectly present every movie as a leader; test independent empty categories.
- Ties can be dropped by selecting only the first maximum; test every tied movie appears.
- Ratings and flagged reviews can be interpreted inconsistently; test ratings are excluded and flagged reviews remain included.

---

### Task 1: Add Story 5 admin acceptance tests

**Files:**
- Modify: `movies/tests.py`

**Interfaces:**
- Consumes: current `Movie`, `Review`, `Rating`, `Order`, and `Item` models.
- Produces: regression coverage for `/admin/movies/movieleaders/` and the report context/template.

- [x] **Step 1: Add a `MovieLeadersAdminTests` fixture and helpers**

Create a superuser, two movies, and helpers for creating an order/item with a chosen quantity and a review with a chosen `flagged` value. Set the report URL to `/admin/movies/movieleaders/`.

- [x] **Step 2: Add the independent leader and quantity tests**

Cover one movie leading both metrics, different movies leading each metric, and purchase totals summing multiple `Item.quantity` values across orders. Assert both leader names and displayed counts.

- [x] **Step 3: Add ties, empty states, and source-data refresh tests**

Assert all tied leaders appear, each empty category renders its own message, and a later request reflects added purchase/review rows. Include a rating-only case and a flagged review to pin metric semantics.

- [x] **Step 4: Add admin access and discoverability tests**

Assert a superuser can load the report and sees its admin index entry; assert a non-staff user is redirected or denied by Django admin.

- [x] **Step 5: Run the focused tests and confirm they fail before implementation**

Run: `python3 manage.py test movies.tests.MovieLeadersAdminTests`

Expected: tests fail because the proxy/report is not currently registered. If Django is unavailable in the default interpreter, identify the project Python environment before continuing; do not install dependencies as part of this feature.

### Task 2: Restore the proxy model and admin report

**Files:**
- Modify: `movies/models.py`
- Modify: `movies/admin.py`
- Create: `movies/templates/admin/movies/movieleaders/movie_leaders.html`

**Interfaces:**
- Consumes: Story 5 contract in the design spec and the existing `0007_movieleaders` proxy migration.
- Produces: `MovieLeaders(Movie)` proxy and a Django admin changelist with context keys `most_purchased_movies`, `purchase_count`, `most_reviewed_movies`, and `review_count`.

- [x] **Step 1: Restore `MovieLeaders` as a `Movie` proxy**

Set `proxy = True`, `verbose_name = "Movie Leaders"`, and `verbose_name_plural = "Movie Leaders"` so the model matches migration 0007 without creating a table.

- [x] **Step 2: Implement independent per-movie aggregates in `MovieLeadersAdmin`**

Use correlated subqueries from `Item` grouped by `movie_id` and from `Review` grouped by `movie_id`, with `Coalesce(..., 0)` for movies with no rows. Order movies by name and primary key, find each positive maximum, and include every movie tied at that maximum. Disable add and delete actions for the report.

- [x] **Step 3: Render the two report sections and empty states**

Create a template extending `admin/base_site.html` with separate Most Purchased and Most Reviewed tables, their counts, breadcrumbs, and the exact empty-state messages `No purchases yet.` and `No reviews yet.`.

- [x] **Step 4: Register the proxy with the custom admin class**

Register `MovieLeaders` in `movies/admin.py`, following the existing `TopReviewerAdmin` report pattern.

- [x] **Step 5: Run focused Story 5 tests**

Run: `python3 manage.py test movies.tests.MovieLeadersAdminTests`

Expected: all Story 5 cases pass, including staff access, index discoverability, ties, empty data, independent leaders, and quantity totals.

### Task 3: Run quick regression checks and prepare the admin reproduction path

**Files:**
- No additional product files; use the report template and existing admin registrations.

**Interfaces:**
- Consumes: completed Movie Leaders report and the existing registered `Movie`, `Review`, `Order`, and `Item` admin models.
- Produces: verified test output and a concise set of manual admin steps for reproducing the report.

- [x] **Step 1: Run focused Story 5 tests and existing movie/cart tests**

Run: `python3 manage.py test movies.tests.MovieLeadersAdminTests cart.tests`

Expected: all focused Story 5 and cart admin tests pass. If the default interpreter lacks Django, use the previously identified project environment without installing dependencies.

- [x] **Step 2: Check model and migration consistency**

Run: `python3 manage.py makemigrations --check --dry-run movies`

Expected: `No changes detected`; the proxy model matches the existing migration.

- [x] **Step 3: Document and inspect the admin reproduction path**

The design spec records the manual admin data-entry sequence. Confirm the local `/admin/` route on port `3000` reaches Django's login screen; the report itself is verified through authenticated Django test-client requests. Do not change the local database or guess credentials to sign into the existing server.

- [x] **Step 4: Inspect the final patch**

Run: `git diff --check && git status --short`

Expected: only the planned report code, tests, and plan/spec artifacts are present; no unrelated files are changed.
