import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image, Alert, ActivityIndicator } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

export default function GradeScreen({ navigation }) {
  const [selectedImage, setSelectedImage] = useState(null);
  const [loading, setLoading] = useState(false);

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

      const response = await axios.post('http://127.0.0.1:8000/grade', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const data = response.data;

      // Add timestamp to result
      const gradedResult = {
        reg_number: data.reg_number,
        score: data.score,
        total: data.total,
        details: data.details,
        timestamp: new Date().toLocaleString(),
      };

      // Save to AsyncStorage
      const existing = await AsyncStorage.getItem('gradedResults');
      const results = existing ? JSON.parse(existing) : [];
      results.push(gradedResult);
      await AsyncStorage.setItem('gradedResults', JSON.stringify(results));

      Alert.alert("Grading Complete", `Reg No: ${gradedResult.reg_number}\nScore: ${gradedResult.score}/${gradedResult.total}`);

      navigation.navigate('Results');
    } catch (error) {
      console.error(error);
      Alert.alert("Error", "Failed to grade the image. Check your backend.");
    } finally {
      setLoading(false);
    }
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
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'flex-start', alignItems: 'center', padding: 20, backgroundColor: 'white' },
  title: { fontSize: 20, fontWeight: 'bold', marginTop: 40, marginBottom: 10 },
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
});
