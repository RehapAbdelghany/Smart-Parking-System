import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/locale_provider.dart';
import '../utils/app_strings.dart';
import 'booking_history_page.dart';
import 'login_page.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      context.read<AuthProvider>().fetchProfile();
    });
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final locale = context.watch<LocaleProvider>();
    final user = auth.user;
    final lang = locale.locale.languageCode;
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Directionality(
      textDirection: lang == 'ar' ? TextDirection.rtl : TextDirection.ltr,
      child: Scaffold(
        appBar: AppBar(
          title: Text(AppStrings.get('myProfile', lang)),
        ),
        body: auth.isLoading
            ? Center(child: CircularProgressIndicator(color: theme.colorScheme.primary))
            : SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    const SizedBox(height: 10),
                    CircleAvatar(
                      radius: 45,
                      backgroundColor: theme.colorScheme.primary,
                      child: Text(_getInitials(user),
                          style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: Colors.white)),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      user != null ? '${user.firstName} ${user.lastName}'.trim() : 'User',
                      style: theme.textTheme.headlineMedium,
                    ),
                    const SizedBox(height: 4),
                    Text(user?.email ?? '', style: theme.textTheme.bodyMedium),
                    const SizedBox(height: 4),
                    Text('@${user?.username ?? ''}', style: theme.textTheme.bodySmall),
                    const SizedBox(height: 30),

                    _buildMenuCard(
                      theme: theme,
                      icon: Icons.history,
                      title: AppStrings.get('myBookings', lang),
                      subtitle: AppStrings.get('bookingHistory', lang),
                      color: theme.colorScheme.primary,
                      onTap: () => Navigator.push(context,
                          MaterialPageRoute(builder: (_) => const BookingHistoryPage())),
                    ),
                    const SizedBox(height: 12),

                    _buildMenuCard(
                      theme: theme,
                      icon: Icons.language,
                      title: AppStrings.get('language', lang),
                      subtitle: lang == 'ar' ? 'Switch to English' : 'التبديل للعربية',
                      color: Colors.purple,
                      onTap: () => locale.toggleLanguage(),
                    ),
                    const SizedBox(height: 12),

                    // Dark Mode Toggle
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: theme.cardColor,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: theme.dividerColor),
                      ),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              color: Colors.indigo.withOpacity(0.1),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Icon(Icons.dark_mode, color: Colors.indigo, size: 24),
                          ),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Text(AppStrings.get('darkMode', lang),
                                style: theme.textTheme.titleMedium),
                          ),
                          Switch(
                            value: locale.isDarkMode,
                            onChanged: (_) => locale.toggleDarkMode(),
                            activeColor: theme.colorScheme.primary,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),

                    _buildMenuCard(
                      theme: theme,
                      icon: Icons.person_outline,
                      title: AppStrings.get('accountInfo', lang),
                      subtitle: user != null
                          ? 'Username: ${user.username}\nEmail: ${user.email}'
                          : 'Not available',
                      color: Colors.blue,
                      onTap: null,
                    ),
                    const SizedBox(height: 30),

                    SizedBox(
                      width: double.infinity, height: 52,
                      child: ElevatedButton.icon(
                        onPressed: () => _logout(context, lang),
                        icon: const Icon(Icons.logout),
                        label: Text(AppStrings.get('logout', lang),
                            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFFE53935),
                          foregroundColor: Colors.white,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
      ),
    );
  }

  String _getInitials(dynamic user) {
    if (user == null) return 'U';
    final f = user.firstName.isNotEmpty ? user.firstName[0] : '';
    final l = user.lastName.isNotEmpty ? user.lastName[0] : '';
    if (f.isEmpty && l.isEmpty) return user.username.isNotEmpty ? user.username[0].toUpperCase() : 'U';
    return '$f$l'.toUpperCase();
  }

  Widget _buildMenuCard({
    required ThemeData theme,
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    VoidCallback? onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: theme.cardColor,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: theme.dividerColor),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: color, size: 24),
            ),
            const SizedBox(width: 14),
            Expanded(child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: theme.textTheme.titleMedium),
                const SizedBox(height: 2),
                Text(subtitle, style: theme.textTheme.bodySmall),
              ],
            )),
            if (onTap != null) Icon(Icons.chevron_right, color: theme.textTheme.bodySmall?.color),
          ],
        ),
      ),
    );
  }

  Future<void> _logout(BuildContext context, String lang) async {
    final theme = Theme.of(context);
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: theme.cardColor,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Text(AppStrings.get('logout', lang)),
        content: Text(AppStrings.get('logoutConfirm', lang)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false),
              child: Text(AppStrings.get('cancel', lang))),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: Text(AppStrings.get('logout', lang), style: const TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
    if (confirm == true && mounted) {
      await context.read<AuthProvider>().logout();
      if (mounted) {
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(builder: (_) => const LoginPage()), (route) => false);
      }
    }
  }
}
