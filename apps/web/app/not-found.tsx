import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center text-center space-y-4 bg-background">
      <div className="text-5xl font-bold text-muted-foreground">404</div>
      <h1 className="text-xl font-semibold">Page not found</h1>
      <p className="text-sm text-muted-foreground">The page you&apos;re looking for doesn&apos;t exist.</p>
      <Link href="/dashboard" className="text-sm text-primary hover:underline">
        Go to Dashboard
      </Link>
    </div>
  );
}
