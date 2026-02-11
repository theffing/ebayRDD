"""
Simple desktop CRUD app for the `ebay_db` PostgreSQL database.

Features:
- Create, Read, Update, Delete for the `user_account` table.
- Prebuilt advanced queries (set ops, CTEs, OLAP, percentiles) with one-click execution.
- Uses Tkinter (stdlib) for UI and psycopg2 for DB access.

Setup:
  pip install psycopg2-binary
  sudo apt-get install python3-tk  # for Tkinter GUI
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
from functools import partial

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    sys.stderr.write(
        "psycopg2-binary is required. Install with: pip install psycopg2-binary\n"
    )
    sys.exit(1)


def get_conn():
    """
    Build a connection using env vars. If no PGHOST is provided, connect via
    UNIX socket (peer auth) instead of TCP localhost to avoid password prompts
    on default local installs.
    """
    host = os.getenv("PGHOST", "")
    return psycopg2.connect(
        host=host if host else None,  # None -> use UNIX socket default
        port=int(os.getenv("PGPORT", "5432")),
        user=os.getenv("PGUSER", os.getenv("USER")),
        password=os.getenv("PGPASSWORD"),
        dbname=os.getenv("PGDATABASE", "ebay_db"),
    )


class CrudApp:
    def __init__(self, root):
        self.root = root
        self.root.title("eBay Mimic - User CRUD")
        self.conn = get_conn()
        self.selected_id = None
        self.query_defs = self._build_queries()

        # UI layout
        self.listbox = tk.Listbox(root, width=70, height=12)
        self.listbox.grid(row=0, column=0, columnspan=4, padx=8, pady=8, sticky="nsew")
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        # Form fields
        self._add_label_entry("Username", 1, "username")
        self._add_label_entry("Email", 2, "email")
        self._add_label_entry("User Type (buyer/seller/both)", 3, "user_type")
        self._add_label_entry("Status (active/suspended/closed)", 4, "account_status")
        self._add_label_entry("Rating (0-5)", 5, "rating")

        # Buttons
        tk.Button(root, text="Create", command=self.create).grid(row=6, column=0, padx=6, pady=8, sticky="ew")
        tk.Button(root, text="Update", command=self.update).grid(row=6, column=1, padx=6, pady=8, sticky="ew")
        tk.Button(root, text="Delete", command=self.delete).grid(row=6, column=2, padx=6, pady=8, sticky="ew")
        tk.Button(root, text="Refresh", command=self.refresh).grid(row=6, column=3, padx=6, pady=8, sticky="ew")

        # Advanced queries panel
        queries_frame = tk.LabelFrame(root, text="Advanced Analytics / Demo Queries")
        queries_frame.grid(row=7, column=0, columnspan=4, padx=8, pady=8, sticky="nsew")

        btn_frame = tk.Frame(queries_frame)
        btn_frame.grid(row=0, column=0, padx=4, pady=4, sticky="ns")

        for i, (key, meta) in enumerate(self.query_defs.items()):
            tk.Button(btn_frame, text=meta["label"], command=partial(self.run_query, key), width=32, anchor="w")\
                .grid(row=i, column=0, padx=2, pady=2, sticky="ew")

        self.output = tk.Text(queries_frame, width=100, height=15, wrap="none")
        self.output.grid(row=0, column=1, padx=4, pady=4, sticky="nsew")
        queries_frame.grid_columnconfigure(1, weight=1)
        queries_frame.grid_rowconfigure(0, weight=1)

        # Menu with quick access to queries
        menubar = tk.Menu(root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Refresh", command=self.refresh)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        q_menu = tk.Menu(menubar, tearoff=0)
        for key, meta in self.query_defs.items():
            q_menu.add_command(label=meta["label"], command=partial(self.run_query, key))
        menubar.add_cascade(label="Queries", menu=q_menu)
        root.config(menu=menubar)

        # Configure resizing
        for col in range(4):
            root.grid_columnconfigure(col, weight=1)
        root.grid_rowconfigure(0, weight=1)
        root.grid_rowconfigure(7, weight=1)

        self.refresh()

    def _add_label_entry(self, text, row, attr):
        tk.Label(self.root, text=text).grid(row=row, column=0, padx=6, pady=4, sticky="w")
        entry = tk.Entry(self.root, width=50)
        entry.grid(row=row, column=1, columnspan=3, padx=6, pady=4, sticky="ew")
        setattr(self, f"{attr}_entry", entry)

    def refresh(self):
        self.listbox.delete(0, tk.END)
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT user_id, username, email, user_type, account_status, rating "
                "FROM user_account ORDER BY user_id"
            )
            rows = cur.fetchall()
            for r in rows:
                display = f"[{r['user_id']}] {r['username']:12} | {r['email']:25} | {r['user_type']:6} | {r['account_status']:9} | rating={r['rating']}"
                self.listbox.insert(tk.END, display)
        self.selected_id = None
        self._clear_form()

    def on_select(self, event):
        if not self.listbox.curselection():
            return
        idx = self.listbox.curselection()[0]
        text = self.listbox.get(idx)
        # Expect format: [id] username ...
        try:
            self.selected_id = int(text.split("]")[0].strip("["))
        except Exception:
            self.selected_id = None
            return
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT user_id, username, email, user_type, account_status, rating "
                "FROM user_account WHERE user_id = %s",
                (self.selected_id,),
            )
            row = cur.fetchone()
            if row:
                self.username_entry.delete(0, tk.END)
                self.username_entry.insert(0, row["username"])
                self.email_entry.delete(0, tk.END)
                self.email_entry.insert(0, row["email"])
                self.user_type_entry.delete(0, tk.END)
                self.user_type_entry.insert(0, row["user_type"])
                self.account_status_entry.delete(0, tk.END)
                self.account_status_entry.insert(0, row["account_status"])
                self.rating_entry.delete(0, tk.END)
                self.rating_entry.insert(0, str(row["rating"]))

    def _clear_form(self):
        for entry in [
            self.username_entry,
            self.email_entry,
            self.user_type_entry,
            self.account_status_entry,
            self.rating_entry,
        ]:
            entry.delete(0, tk.END)

    def _build_queries(self):
        """
        Returns a dict of advanced/demo queries demonstrating:
        - set operations (UNION/EXCEPT)
        - set membership (IN)
        - set comparison (ALL)
        - CTE (WITH)
        - advanced aggregates (percentile_cont)
        - OLAP (ROLLUP/CUBE)
        """
        return {
            "union_buyers_sellers": {
                "label": "Set: buyers UNION sellers",
                "sql": """
                    SELECT username, 'buyer'  AS role FROM user_account WHERE user_type IN ('buyer','both')
                    UNION
                    SELECT username, 'seller' AS role FROM user_account WHERE user_type IN ('seller','both')
                    ORDER BY username, role;
                """,
                "desc": "UNION of buyers and sellers (set operation)",
            },
            "except_never_bidded": {
                "label": "Set: users NEVER bid (EXCEPT)",
                "sql": """
                    SELECT username FROM user_account
                    EXCEPT
                    SELECT DISTINCT u.username
                    FROM user_account u JOIN bid b ON b.user_id = u.user_id
                    ORDER BY username;
                """,
                "desc": "Users who have never placed a bid (EXCEPT)",
            },
            "membership_watch_phones": {
                "label": "Membership: watchers of Phones/Laptops",
                "sql": """
                    SELECT DISTINCT u.username, l.title, c.name AS category
                    FROM user_listing_watch w
                    JOIN listing l ON l.listing_id = w.listing_id
                    JOIN category c ON c.category_id = l.category_id
                    JOIN user_account u ON u.user_id = w.user_id
                    WHERE c.name IN ('Phones','Laptops')
                    ORDER BY username, title;
                """,
                "desc": "IN membership on categories Phones/Laptops",
            },
            "set_comparison_all": {
                "label": "Set comparison: start_price > ALL bids",
                "sql": """
                    SELECT l.listing_id, l.title, l.start_price
                    FROM listing l
                    WHERE l.start_price > ALL (
                        SELECT b.bid_amount FROM bid b WHERE b.listing_id = l.listing_id
                    )
                    ORDER BY l.listing_id;
                """,
                "desc": "Listings whose start price exceeds all existing bids (ALL)",
            },
            "cte_top_watchers": {
                "label": "CTE: top watchers per listing",
                "sql": """
                    WITH watch_counts AS (
                        SELECT l.listing_id, l.title, COUNT(w.user_id) AS watchers
                        FROM listing l
                        LEFT JOIN user_listing_watch w ON w.listing_id = l.listing_id
                        GROUP BY l.listing_id, l.title
                    )
                    SELECT * FROM watch_counts
                    ORDER BY watchers DESC, listing_id
                    LIMIT 10;
                """,
                "desc": "CTE to compute watcher counts",
            },
            "agg_percentiles": {
                "label": "Aggregate: bid amount percentiles",
                "sql": """
                    SELECT percentile_cont(ARRAY[0.25,0.5,0.75]) WITHIN GROUP (ORDER BY bid_amount) AS bid_amount_percentiles
                    FROM bid;
                """,
                "desc": "Advanced aggregate: percentile_cont",
            },
            "olap_rollup_revenue_category": {
                "label": "OLAP: revenue by category (ROLLUP)",
                "sql": """
                    SELECT COALESCE(c.name, '**TOTAL**') AS category, 
                           COALESCE(SUM(t.final_price),0) AS revenue
                    FROM category c
                    LEFT JOIN listing l ON l.category_id = c.category_id
                    LEFT JOIN transaction t ON t.listing_id = l.listing_id AND t.payment_status = 'paid'
                    GROUP BY ROLLUP(c.name)
                    ORDER BY CASE WHEN c.name IS NULL THEN 1 ELSE 0 END, revenue DESC;
                """,
                "desc": "ROLLUP creates summary rows (NULL = grand total)",
            },
            "olap_cube_payment_shipping": {
                "label": "OLAP: revenue cube pay/ship",
                "sql": """
                    SELECT COALESCE(payment_status::text, '**ALL**') AS payment_status,
                           COALESCE(shipping_status::text, '**ALL**') AS shipping_status,
                           SUM(final_price) AS revenue
                    FROM transaction
                    GROUP BY CUBE(payment_status, shipping_status)
                    ORDER BY CASE WHEN payment_status IS NULL THEN 1 ELSE 0 END,
                             CASE WHEN shipping_status IS NULL THEN 1 ELSE 0 END,
                             payment_status, shipping_status;
                """,
                "desc": "CUBE creates all combinations (NULL = subtotal/total)",
            },
        }

    def _format_rows(self, rows):
        if not rows:
            return "(no rows)\n"
        # rows is list of dicts
        cols = list(rows[0].keys())
        lines = []
        header = " | ".join(cols)
        lines.append(header)
        lines.append("-" * len(header))
        for r in rows:
            line = " | ".join(str(r[c]) if r[c] is not None else "NULL" for c in cols)
            lines.append(line)
        return "\n".join(lines) + "\n"

    def run_query(self, key):
        meta = self.query_defs.get(key)
        if not meta:
            return
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, f"{meta['label']}\n{meta['desc']}\n\nSQL:\n{meta['sql'].strip()}\n\n")
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(meta["sql"])
                rows = cur.fetchall()
            self.output.insert(tk.END, "Result:\n")
            self.output.insert(tk.END, self._format_rows(rows))
        except Exception as exc:
            self.output.insert(tk.END, f"Error: {exc}\n")

    def create(self):
        username = self.username_entry.get().strip()
        email = self.email_entry.get().strip()
        user_type = self.user_type_entry.get().strip() or "buyer"
        account_status = self.account_status_entry.get().strip() or "active"
        rating = self.rating_entry.get().strip() or 0
        if not username or not email:
            messagebox.showerror("Error", "Username and email are required.")
            return
        if user_type not in ("buyer", "seller", "both"):
            messagebox.showerror("Error", "User type must be buyer, seller, or both.")
            return
        if account_status not in ("active", "suspended", "closed"):
            messagebox.showerror("Error", "Status must be active, suspended, or closed.")
            return
        try:
            rating_val = float(rating)
        except ValueError:
            messagebox.showerror("Error", "Rating must be numeric.")
            return
        if not 0 <= rating_val <= 5:
            messagebox.showerror("Error", "Rating must be between 0 and 5.")
            return
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO user_account (username, email, user_type, account_status, rating)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING user_id
                    """,
                    (username, email, user_type, account_status, rating_val),
                )
                new_id = cur.fetchone()[0]
        self.refresh()
        messagebox.showinfo("Success", f"Created user_id={new_id}")

    def update(self):
        if not self.selected_id:
            messagebox.showerror("Error", "Select a user to update.")
            return
        uid = self.selected_id
        username = self.username_entry.get().strip()
        email = self.email_entry.get().strip()
        user_type = self.user_type_entry.get().strip() or "buyer"
        account_status = self.account_status_entry.get().strip() or "active"
        rating = self.rating_entry.get().strip() or 0
        if not username or not email:
            messagebox.showerror("Error", "Username and email are required.")
            return
        if user_type not in ("buyer", "seller", "both"):
            messagebox.showerror("Error", "User type must be buyer, seller, or both.")
            return
        if account_status not in ("active", "suspended", "closed"):
            messagebox.showerror("Error", "Status must be active, suspended, or closed.")
            return
        try:
            rating_val = float(rating)
        except ValueError:
            messagebox.showerror("Error", "Rating must be numeric.")
            return
        if not 0 <= rating_val <= 5:
            messagebox.showerror("Error", "Rating must be between 0 and 5.")
            return
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE user_account
                       SET username = %s,
                           email = %s,
                           user_type = %s,
                           account_status = %s,
                           rating = %s
                     WHERE user_id = %s
                    """,
                    (username, email, user_type, account_status, rating_val, uid),
                )
        self.refresh()
        messagebox.showinfo("Success", f"Updated user_id={uid}")

    def delete(self):
        if not self.selected_id:
            messagebox.showerror("Error", "Select a user to delete.")
            return
        if not messagebox.askyesno("Confirm", f"Delete user_id={self.selected_id}?"):
            return
        uid = self.selected_id
        try:
            with self.conn:
                with self.conn.cursor() as cur:
                    # Find listings owned by this user
                    cur.execute(
                        "SELECT listing_id FROM listing WHERE seller_id = %s",
                        (uid,),
                    )
                    listing_ids = [row[0] for row in cur.fetchall()]
                    listing_array = listing_ids if listing_ids else [None]

                    # Delete feedback authored/targeted or tied to transactions involving the user/listings
                    cur.execute(
                        """
                        DELETE FROM feedback
                        WHERE author_user_id = %s
                           OR target_user_id = %s
                           OR transaction_id IN (
                                SELECT transaction_id FROM transaction
                                WHERE buyer_id = %s OR seller_id = %s
                                   OR listing_id = ANY(%s)
                           )
                        """,
                        (uid, uid, uid, uid, listing_array),
                    )

                    # Delete transactions involving the user or their listings
                    cur.execute(
                        """
                        DELETE FROM transaction
                        WHERE buyer_id = %s
                           OR seller_id = %s
                           OR listing_id = ANY(%s)
                        """,
                        (uid, uid, listing_array),
                    )

                    # Delete bids placed by the user or on their listings
                    cur.execute(
                        """
                        DELETE FROM bid
                        WHERE user_id = %s
                           OR listing_id = ANY(%s)
                        """,
                        (uid, listing_array),
                    )

                    # Delete watches by the user or on their listings
                    cur.execute(
                        """
                        DELETE FROM user_listing_watch
                        WHERE user_id = %s
                           OR listing_id = ANY(%s)
                        """,
                        (uid, listing_array),
                    )

                    # Delete listings owned by the user
                    cur.execute(
                        "DELETE FROM listing WHERE seller_id = %s",
                        (uid,),
                    )

                    # Finally delete the user
                    cur.execute(
                        "DELETE FROM user_account WHERE user_id = %s",
                        (uid,),
                    )
            self.refresh()
            messagebox.showinfo("Deleted", f"Deleted user_id={uid}")
        except Exception as exc:
            messagebox.showerror("Delete failed", f"{exc}")


def main():
    root = tk.Tk()
    app = CrudApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

