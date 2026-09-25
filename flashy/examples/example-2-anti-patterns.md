# Anti-Patterns: Before / After

Each pair shows an artificial-stop impulse and the corrected behavior under this skill.

---

**Before:**
> "Here's a basic version of the script. You can expand it to handle more file types as needed."

**After:**
> [continues implementing handling for the other file types the user actually asked about, then delivers the complete script]

---

**Before:**
> "This should get you started — the rest of the report sections would follow a similar structure."

**After:**
> [writes the remaining sections in full rather than describing how they'd follow]

---

**Before:**
> "Due to space constraints, I'll just show Part 1 of the implementation."

**After:**
> If this is a genuine context/length limit: uses the Continuation Boundary format (see `templates/continuation_boundary.md`) — states what's done, what's left, and continues in the next turn. If it's not a genuine limit: just keeps building.

---

**Before (inappropriate pause):**
> "I've finished the login form. Should I continue with the rest of the app?"

**After:**
> [continues automatically to the next milestone without asking, since continuing isn't a decision that changes the implementation]

---

**Before (appropriate pause — kept, not corrected):**
> "Before I build the persistence layer, which database do you want — SQLite, Postgres, or an in-memory store? This changes the implementation significantly."

**After:** No correction needed — this is a genuine implementation-changing decision, exactly the kind of pause the skill still allows.
