import { redirect } from "next/navigation";
import { Suspense } from "react";

import { formatDate } from "@/components/format";
import { authedJson, getCurrentUser } from "@/lib/auth";

type Account = {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
};

export default function AdminPage() {
  return (
    <>
      <h1 className="cover-line text-5xl sm:text-6xl">All accounts</h1>
      <Suspense fallback={<p className="text-muted">Loading accounts…</p>}>
        <Accounts />
      </Suspense>
    </>
  );
}

async function Accounts() {
  // The API enforces this too (403); checking first sends a non-admin home
  // instead of to an error page.
  const user = await getCurrentUser();
  if (user.role !== "admin") {
    redirect("/");
  }
  const { users, total } = await authedJson<{ users: Account[]; total: number }>(
    "/admin/users",
  );
  return (
    <section aria-labelledby="account-count" className="flex flex-col gap-3">
      <h2 id="account-count" className="cover-label text-sm text-muted">
        {total} {total === 1 ? "account" : "accounts"}
      </h2>
      <div className="overflow-x-auto">
        <table className="data-table">
          <thead>
            <tr>
              {["Email", "Role", "Status", "Joined"].map((heading) => (
                <th key={heading} scope="col">
                  {heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {users.map((account) => (
              <tr key={account.id}>
                <th scope="row" className="font-semibold">
                  {account.email}
                </th>
                <td className="capitalize">{account.role}</td>
                <td>
                  <span className={`state ${account.is_active ? "state-ready" : "text-muted"}`}>
                    {account.is_active ? "Active" : "Disabled"}
                  </span>
                </td>
                <td className="text-muted">
                  <time dateTime={account.created_at}>{formatDate(account.created_at)}</time>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
