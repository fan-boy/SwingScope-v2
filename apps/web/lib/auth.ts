import { type NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import bcrypt from "bcryptjs";

if (!process.env.AUTH_EMAIL) throw new Error("AUTH_EMAIL env var is required");
if (!process.env.AUTH_PASSWORD_HASH) throw new Error("AUTH_PASSWORD_HASH env var is required");
if (!process.env.NEXTAUTH_SECRET) throw new Error("NEXTAUTH_SECRET env var is required");

export const authOptions: NextAuthOptions = {
  session: { strategy: "jwt" },
  pages: { signIn: "/login" },
  providers: [
    CredentialsProvider({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;

        const allowedEmail = process.env.AUTH_EMAIL!;
        const passwordHash = process.env.AUTH_PASSWORD_HASH!;

        if (credentials.email.toLowerCase() !== allowedEmail.toLowerCase()) return null;

        const valid = await bcrypt.compare(credentials.password, passwordHash);
        if (!valid) return null;

        return { id: "1", email: allowedEmail, name: "Admin" };
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) token.email = user.email;
      return token;
    },
    async session({ session, token }) {
      if (session.user) session.user.email = token.email as string;
      return session;
    },
  },
};
