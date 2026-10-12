export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center gap-6 px-4 py-16">
      <p className="text-2xl font-semibold tracking-tight">Digest</p>
      {children}
    </main>
  );
}
