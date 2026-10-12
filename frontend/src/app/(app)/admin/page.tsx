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
      <h1 className="text-2xl font-semibold tracking-tight">All accounts</h1>
      <Suspense fallback={<p className="text-zinc-500">Loading accounts…</p>}>
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
    <>
      <p className="text-sm text-zinc-600 dark:text-zinc-400">
        {total} {total === 1 ? "account" : "accounts"}
      </p>
      <table className="w-full text-left text-sm">
        <thead className="border-b border-zinc-200 dark:border-zinc-800">
          <tr>
            <th className="py-2 font-medium">Email</th>
            <th className="py-2 font-medium">Role</th>
            <th className="py-2 font-medium">Status</th>
            <th className="py-2 font-medium">Joined</th>
          </tr>
        </thead>
        <tbody>
          {users.map((account) => (
            <tr key={account.id} className="border-b border-zinc-100 dark:border-zinc-900">
              <td className="py-2">{account.email}</td>
              <td className="py-2">{account.role}</td>
              <td className="py-2">{account.is_active ? "active" : "disabled"}</td>
              <td className="py-2">{new Date(account.created_at).toLocaleDateString("en-GB")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
