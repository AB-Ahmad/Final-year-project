// import React, { useState } from 'react';
import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, ScrollView, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function TemplatesScreen() {
  const [courseCode, setCourseCode] = useState('');
  const [answers, setAnswers] = useState(Array(30).fill(''));

  const handleAnswerChange = (text, index) => {
    const updatedAnswers = [...answers];
    updatedAnswers[index] = text.toUpperCase();
    setAnswers(updatedAnswers);
  };

  const handleSave = async () => {
    if (!courseCode.trim()) {
      Alert.alert('Validation Error', 'Course code is required.');
      return;
    }

    if (answers.some((ans) => !['A', 'B', 'C', 'D', 'E'].includes(ans))) {
      Alert.alert('Validation Error', 'Please enter A–E for all answers.');
      return;
    }

    try {
      const existing = await AsyncStorage.getItem('templates');
      const templates = existing ? JSON.parse(existing) : {};

      // Save using course code as key
      templates[courseCode.toUpperCase()] = answers;

      await AsyncStorage.setItem('templates', JSON.stringify(templates));
      Alert.alert('Success', `Template for ${courseCode} saved successfully!`);

      // Clear form
      setCourseCode('');
      setAnswers(Array(30).fill(''));
    } catch (error) {
      Alert.alert('Error', 'Failed to save the template.');
      console.error(error);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Upload Answer Template</Text>

      <TextInput
        placeholder="Enter Course Code"
        value={courseCode}
        onChangeText={setCourseCode}
        style={styles.input}
      />

      <Text style={styles.section}>Enter Correct Answers (A–E)</Text>

      {answers.map((answer, index) => (
        <View key={index} style={styles.questionRow}>
          <Text style={styles.qLabel}>Q{index + 1}:</Text>
          <TextInput
            style={styles.qInput}
            value={answer}
            maxLength={1}
            onChangeText={(text) => handleAnswerChange(text, index)}
            placeholder="A–E"
            autoCapitalize="characters"
          />
        </View>
      ))}

      <TouchableOpacity style={styles.saveButton} onPress={handleSave}>
        <Text style={styles.saveButtonText}>Save Template</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, backgroundColor: 'white' },
  title: { fontSize: 22, fontWeight: 'bold', marginBottom: 20, textAlign: 'center' },
  section: { fontWeight: 'bold', marginTop: 20, marginBottom: 10 },
  input: {
    borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 10, fontSize: 16, backgroundColor: '#f9f9f9'
  },
  questionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 5
  },
  qLabel: { width: 40, fontWeight: '600' },
  qInput: {
    borderWidth: 1,
    borderColor: '#ccc',
    width: 60,
    padding: 8,
    borderRadius: 6,
    backgroundColor: '#f0f0f0',
    textAlign: 'center',
    fontSize: 16
  },
  saveButton: {
    backgroundColor: '#3b82f6',
    padding: 15,
    borderRadius: 10,
    marginTop: 30,
    alignItems: 'center'
  },
  saveButtonText: {
    color: 'white',
    fontWeight: 'bold'
  }
});
