import { redirect } from "next/navigation";
import { Suspense } from "react";

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
      <h1 className="text-4xl font-extrabold tracking-tight">All accounts</h1>
      <Suspense fallback={<p className="text-graphite">Loading accounts…</p>}>
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
      <p id="account-count" className="text-sm text-graphite">
        {total} {total === 1 ? "account" : "accounts"}
      </p>
      <div className="overflow-x-auto rounded-md border border-rule bg-sheet">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-rule text-graphite">
            <tr>
              {["Email", "Role", "Status", "Joined"].map((heading) => (
                <th key={heading} scope="col" className="px-4 py-3 font-medium">
                  {heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-rule">
            {users.map((account) => (
              <tr key={account.id}>
                <th scope="row" className="px-4 py-3 font-semibold">
                  {account.email}
                </th>
                <td className="px-4 py-3 capitalize">{account.role}</td>
                <td className="px-4 py-3">
                  <span className="inline-flex items-center gap-2">
                    <span
                      aria-hidden
                      className={`size-2 rounded-full ${account.is_active ? "bg-settled" : "bg-rule"}`}
                    />
                    {account.is_active ? "Active" : "Disabled"}
                  </span>
                </td>
                <td className="px-4 py-3 text-graphite">
                  {new Date(account.created_at).toLocaleDateString("en-GB")}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
