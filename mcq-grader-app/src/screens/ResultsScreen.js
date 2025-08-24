import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image, Alert, ActivityIndicator, FlatList } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { BASE_URL } from '../../config';

export default function ResultsScreen({ navigation }) {
  const [selectedImage, setSelectedImage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);

  // 🔹 Load saved results every time screen is focused
  useEffect(() => {
    const loadResults = async () => {
      try {
        const stored = await AsyncStorage.getItem('gradedResults');
        if (stored) {
          setResults(JSON.parse(stored));
        } else {
          setResults([]);
        }
      } catch (error) {
        console.error("Failed to load results", error);
      }
    };

    const unsubscribe = navigation.addListener("focus", loadResults);
    loadResults(); // run once on mount
    return unsubscribe;
  }, [navigation]);

  const pickImage = async () => {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert("Permission Required", "Please allow access to your photo library.");
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 1,
      base64: false,
    });

    if (!result.canceled) {
      setSelectedImage(result.assets[0].uri);
    }
  };

  const gradeImage = async () => {
    if (!selectedImage) {
      Alert.alert("No Image Selected", "Please select an image first.");
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', {
        uri: selectedImage,
        type: 'image/jpeg',
        name: 'answer_sheet.jpg',
      });

      const response = await axios.post(`${BASE_URL}/grade`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const data = response.data;

      if (!data || !data.answers) {
        throw new Error("Invalid grading response");
      }

      const gradedResult = {
        reg_number: data.reg_number,
        score: data.score,
        total: data.total,
        details: data.details,
        debug_image: data.debug_image || null, // ✅ ensure debug image is included
        timestamp: new Date().toLocaleString(),
      };

      // Save to AsyncStorage
      const existing = await AsyncStorage.getItem('gradedResults');
      const allResults = existing ? JSON.parse(existing) : [];
      allResults.push(gradedResult);
      await AsyncStorage.setItem('gradedResults', JSON.stringify(allResults));

      setResults(allResults);

      // 🔹 Navigate to full result screen
      navigation.navigate('GradingResult', { result: gradedResult });

    } catch (error) {
      console.error(error);
      Alert.alert("Error", error.message);
    } finally {
      setLoading(false);
    }
  };

  const clearResults = async () => {
    Alert.alert("Confirm", "Are you sure you want to clear all graded results?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Clear",
        style: "destructive",
        onPress: async () => {
          await AsyncStorage.removeItem("gradedResults");
          setResults([]); // update UI immediately
        }
      }
    ]);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Upload Answer Sheet</Text>
      <Text style={styles.subtitle}>Use camera or gallery to upload scanned MCQ sheet.</Text>

      <TouchableOpacity style={styles.button} onPress={pickImage}>
        <Text style={styles.buttonText}>📷 Select Image</Text>
      </TouchableOpacity>

      {selectedImage && (
        <>
          <Image source={{ uri: selectedImage }} style={styles.imagePreview} resizeMode="contain" />
          <TouchableOpacity style={[styles.button, { backgroundColor: '#10b981' }]} onPress={gradeImage}>
            <Text style={styles.buttonText}>Grade Now</Text>
          </TouchableOpacity>
        </>
      )}

      {loading && <ActivityIndicator size="large" color="#3b82f6" style={{ marginTop: 20 }} />}

      {/* 🔹 Results Section */}
      <Text style={[styles.title, { marginTop: 30 }]}>Saved Results</Text>

      {results.length === 0 ? (
        <Text style={styles.subtitle}>No results saved yet.</Text>
      ) : (
        <>
          <FlatList
            data={results}
            keyExtractor={(item, index) => index.toString()}
            renderItem={({ item }) => (
              <View style={styles.resultCard}>
                <Text style={styles.resultText}>Reg No: {item.reg_number}</Text>
                <Text style={styles.resultText}>Score: {item.score}/{item.total}</Text>
                <Text style={styles.resultText}>Date: {item.timestamp}</Text>

                {item.debug_image && (
                  <Image
                    source={{ uri: `data:image/jpeg;base64,${item.debug_image}` }}
                    style={styles.resultImage}
                    resizeMode="contain"
                  />
                )}
              </View>
            )}
          />

          <TouchableOpacity style={[styles.button, { backgroundColor: '#ef4444' }]} onPress={clearResults}>
            <Text style={styles.buttonText}>🗑️ Clear All Results</Text>
          </TouchableOpacity>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'flex-start', alignItems: 'center', padding: 20, backgroundColor: 'white' },
  title: { fontSize: 20, fontWeight: 'bold', marginTop: 20, marginBottom: 10 },
  subtitle: { color: 'gray', marginBottom: 20, textAlign: 'center' },
  button: { backgroundColor: '#3b82f6', padding: 15, borderRadius: 10, width: '80%', marginBottom: 20 },
  buttonText: { color: 'white', textAlign: 'center', fontWeight: 'bold' },
  imagePreview: {
    width: '100%',
    height: 400,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#ccc',
    marginTop: 10,
  },
  resultCard: {
    backgroundColor: '#f3f4f6',
    padding: 15,
    borderRadius: 10,
    marginVertical: 8,
    width: '100%',
  },
  resultText: { fontSize: 16, marginBottom: 4 },
  resultImage: {
    width: "100%",
    height: 200,
    marginTop: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#ccc",
  },
});
