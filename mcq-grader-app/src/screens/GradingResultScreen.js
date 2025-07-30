import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function ResultsScreen() {
  const [results, setResults] = useState([]);

  // Load results from storage on screen load
  useEffect(() => {
    const loadResults = async () => {
      try {
        const storedResults = await AsyncStorage.getItem('gradedResults');
        if (storedResults) {
          setResults(JSON.parse(storedResults));
        }
      } catch (error) {
        console.error('Error loading results:', error);
      }
    };
    loadResults();
  }, []);

  const clearResults = async () => {
    Alert.alert('Confirm', 'Are you sure you want to clear all results?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Clear',
        onPress: async () => {
          await AsyncStorage.removeItem('gradedResults');
          setResults([]);
        },
        style: 'destructive',
      },
    ]);
  };

  const renderItem = ({ item }) => (
    <View style={styles.resultCard}>
      <Text style={styles.regNumber}>Reg No: {item.reg_number}</Text>
      <Text style={styles.score}>Score: {item.score}/{item.total}</Text>
      <Text style={styles.timestamp}>Date: {item.timestamp}</Text>
    </View>
  );

  return (
    <View style={styles.container}>
      {results.length === 0 ? (
        <Text style={styles.noResults}>No graded results yet. Grade some scripts to see them here.</Text>
      ) : (
        <FlatList
          data={results}
          renderItem={renderItem}
          keyExtractor={(item, index) => index.toString()}
        />
      )}

      {results.length > 0 && (
        <TouchableOpacity style={styles.clearButton} onPress={clearResults}>
          <Text style={styles.clearButtonText}>Clear All Results</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: 'white' },
  noResults: { textAlign: 'center', marginTop: 50, color: 'gray' },
  resultCard: {
    padding: 15,
    backgroundColor: '#f9f9f9',
    borderRadius: 10,
    marginVertical: 8,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  regNumber: { fontWeight: 'bold', fontSize: 16 },
  score: { marginTop: 5, color: '#3b82f6', fontWeight: '600' },
  timestamp: { marginTop: 5, color: 'gray', fontSize: 12 },
  clearButton: {
    backgroundColor: 'red',
    padding: 15,
    borderRadius: 10,
    marginTop: 20,
    alignItems: 'center',
  },
  clearButtonText: { color: 'white', fontWeight: 'bold' },
});
