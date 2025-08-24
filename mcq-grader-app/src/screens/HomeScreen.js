import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function HomeScreen({ navigation }) {
  const [templateCount, setTemplateCount] = useState(0);
  const [resultsCount, setResultsCount] = useState(0);

  // 🔹 Load counts whenever screen comes into focus
  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', async () => {
      try {
        const storedTemplates = await AsyncStorage.getItem('templates');
        const storedResults = await AsyncStorage.getItem('gradedResults');

        const templates = storedTemplates ? JSON.parse(storedTemplates) : {};
        const results = storedResults ? JSON.parse(storedResults) : [];

        setTemplateCount(Object.keys(templates).length);
        setResultsCount(results.length);
      } catch (error) {
        console.error("Error loading counts:", error);
      }
    });

    return unsubscribe;
  }, [navigation]);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>MCQ Grading System</Text>
      <Text style={styles.subtitle}>Create templates, grade scripts, and manage results</Text>

      <View style={styles.statsContainer}>
        <View style={styles.statBox}>
          <Text style={styles.statNumber}>{templateCount}</Text>
          <Text style={styles.statLabel}>Templates</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={styles.statNumber}>{resultsCount}</Text>
          <Text style={styles.statLabel}>Results</Text>
        </View>
      </View>

      <TouchableOpacity
        style={[styles.button, { backgroundColor: '#3b82f6' }]}
        onPress={() => navigation.navigate('Templates')}
      >
        <Text style={styles.buttonText}>+ New Template</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.button, { backgroundColor: '#c084fc' }]}
        onPress={() => navigation.navigate('Results')}
      >
        <Text style={styles.buttonText}>Grade Scripts</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff', padding: 20, justifyContent: 'center' },
  title: { fontSize: 24, fontWeight: 'bold', textAlign: 'center', marginBottom: 4 },
  subtitle: { textAlign: 'center', color: '#666', marginBottom: 30 },
  statsContainer: { flexDirection: 'row', justifyContent: 'space-around', marginBottom: 40 },
  statBox: {
    backgroundColor: '#f3f4f6',
    paddingVertical: 20,
    paddingHorizontal: 25,
    borderRadius: 12,
    alignItems: 'center',
    width: '40%',
  },
  statNumber: { fontSize: 22, fontWeight: 'bold', marginBottom: 4, color: '#3b82f6' },
  statLabel: { fontSize: 14, color: '#333' },
  button: { paddingVertical: 15, borderRadius: 10, marginVertical: 8, width: '100%', alignSelf: 'center' },
  buttonText: { color: 'white', textAlign: 'center', fontWeight: 'bold', fontSize: 16 },
});
