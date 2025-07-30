import React, { useState } from 'react';
import { View, Text, Switch, TouchableOpacity, StyleSheet } from 'react-native';

export default function SettingsScreen() {
  const [isDarkMode, setIsDarkMode] = useState(false);

  return (
    <View style={styles.container}>
      <Text style={styles.section}>Appearance</Text>
      <View style={styles.row}>
        <Text>Dark Mode</Text>
        <Switch value={isDarkMode} onValueChange={setIsDarkMode} />
      </View>

      <Text style={styles.section}>Data Management</Text>
      <TouchableOpacity>
        <Text style={styles.clearText}>Clear All Data</Text>
      </TouchableOpacity>

      <Text style={styles.section}>About</Text>
      <Text>Version: 1.0.0</Text>
      <Text>Help & Support</Text>
      <Text>Contact Us</Text>
      <Text>Visit Website</Text>

      <Text style={styles.footer}>MCQ Grading System © 2025</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: 'white' },
  section: { fontSize: 18, fontWeight: 'bold', marginTop: 20 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginVertical: 10 },
  clearText: { color: 'red', marginVertical: 10 },
  footer: { marginTop: 40, textAlign: 'center', color: 'gray' }
});
