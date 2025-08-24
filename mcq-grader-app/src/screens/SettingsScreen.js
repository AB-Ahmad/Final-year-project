// SettingsScreen.js
import React, { useState } from 'react';
import { View, Text, Switch, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function SettingsScreen() {
  const [isDarkMode, setIsDarkMode] = useState(false);

  // 🔹 Handle full reset
  const handleResetApp = () => {
    Alert.alert(
      "Confirm Reset",
      "This will clear ALL templates and results. Are you sure?",
      [
        { text: "Cancel", style: "cancel" },
        { 
          text: "Reset",
          style: "destructive",
          onPress: async () => {
            try {
              await AsyncStorage.removeItem("templates");
              await AsyncStorage.removeItem("gradedResults");
              Alert.alert("Success", "App has been reset successfully!");
            } catch (error) {
              Alert.alert("Error", "Failed to reset app.");
              console.error(error);
            }
          }
        }
      ]
    );
  };

  return (
    <View style={styles.container}>
      <Text style={styles.section}>Appearance</Text>
      <View style={styles.row}>
        <Text>Dark Mode</Text>
        <Switch value={isDarkMode} onValueChange={setIsDarkMode} />
      </View>

      <Text style={styles.section}>Data Management</Text>
      <TouchableOpacity onPress={handleResetApp}>
        <Text style={styles.clearText}>Reset App (Clear Templates & Results)</Text>
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
  clearText: { color: 'red', marginVertical: 10, fontWeight: "bold" },
  footer: { marginTop: 40, textAlign: 'center', color: 'gray' }
});
