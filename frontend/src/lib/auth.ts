import NextAuth from "next-auth";
import GitHub from "next-auth/providers/github";

export const { handlers, signIn, signOut, auth } = NextAuth({
	providers: [
		GitHub({
			clientId: process.env.AUTH_GITHUB_ID,
			clientSecret: process.env.AUTH_GITHUB_SECRET,
		}),
	],
	pages: {
		signIn: "/login",
	},
	callbacks: {
		async jwt({ token, account, profile }) {
			if (account && profile) {
				token.provider = account.provider;
				token.providerId = profile.sub || String(profile.id);
			}
			return token;
		},
		async session({ session, token }) {
			if (token) {
				session.user.id = token.sub as string;
			}
			return session;
		},
	},
});
