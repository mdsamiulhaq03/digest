import { getDemoAccounts } from "@/lib/demo";

import { demoLogin } from "./actions";

const LABELS = { user: "Log in as demo user", admin: "Log in as admin" } as const;

export async function DemoButtons() {
  const accounts = await getDemoAccounts();
  if (accounts.length === 0) {
    return null;
  }
  return (
    <section className="flex flex-col gap-2 border-t border-zinc-200 pt-6 dark:border-zinc-800">
      <p className="text-sm text-zinc-600 dark:text-zinc-400">Just looking around?</p>
      {accounts.map((account) => (
        <form key={account.role} action={demoLogin.bind(null, account.role)}>
          <button
            type="submit"
            className="w-full rounded border border-zinc-300 px-4 py-2 text-sm font-medium dark:border-zinc-700"
          >
            {LABELS[account.role]}
            <span className="block text-xs font-normal text-zinc-500">{account.email}</span>
          </button>
        </form>
      ))}
    </section>
  );
}
