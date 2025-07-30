import React, { useState } from 'react';
import {
  View,
  Text,
  Button,
  Image,
  ActivityIndicator,
  Alert,
  Platform
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { API_URL } from '../../config'; // adjust path if needed

const GradeScreen = () => {
  const [image, setImage] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const pickFromGallery = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 1,
    });

    if (!result.canceled && result.assets?.length > 0) {
      setImage(result.assets[0].uri);
      setResult(null);
    }
  };

  const takePhoto = async () => {
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) {
      Alert.alert('Permission Denied', 'Camera access is required to take a photo.');
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      quality: 1,
    });

    if (!result.canceled && result.assets?.length > 0) {
      setImage(result.assets[0].uri);
      setResult(null);
    }
  };

  const uploadImage = async () => {
    if (!image) {
      Alert.alert('No image selected', 'Please pick or take an image first.');
      return;
    }

    setLoading(true);

    const fileUri = Platform.OS === 'ios' ? image.replace('file://', '') : image;

    const formData = new FormData();
    formData.append('file', {
      uri: fileUri,
      type: 'image/jpeg',
      name: 'mcq.jpg',
    });

    try {
      const response = await fetch(`${API_URL}/grade`, {
        method: 'POST',
        body: formData,
        headers: {
          Accept: 'application/json',
        },
      });

      console.log('📤 Sent to:', `${API_URL}/grade`);
      console.log('📎 Image URI:', image);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Server responded with error:', errorText);
        throw new Error(errorText || 'Upload failed');
      }

      const data = await response.json();
      console.log('✅ Server response:', data);
      setResult(data);
    } catch (error) {
      console.error('🛑 Upload error (full):', error);
      Alert.alert('Error', error.message || 'Upload failed. Check server and image.');
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async () => {
    try {
      const res = await fetch(`${API_URL}/docs`);
      Alert.alert('Backend Connected', `Status: ${res.status}`);
    } catch (err) {
      Alert.alert('Connection Failed', err.message);
    }
  };

  return (
    <View style={{ flex: 1, padding: 20 }}>
      <Text style={{ fontSize: 18, fontWeight: 'bold', marginBottom: 10 }}>
        Upload or Take Answer Sheet Photo
      </Text>

      <Button title="📂 Pick from Gallery" onPress={pickFromGallery} />
      <View style={{ marginVertical: 10 }}>
        <Button title="📸 Take Photo with Camera" onPress={takePhoto} color="#6366f1" />
      </View>
      <View style={{ marginVertical: 10 }}>
        <Button title="🔌 Test Backend Connection" onPress={testConnection} color="#f59e0b" />
      </View>

      {image && (
        <>
          <Image
            source={{ uri: image }}
            style={{ width: '100%', height: 300, marginVertical: 10, borderRadius: 10 }}
            resizeMode="contain"
          />
          <Button title="🚀 Upload and Grade" onPress={uploadImage} color="#22c55e" />
        </>
      )}

      {loading && <ActivityIndicator size="large" color="#3b82f6" style={{ marginTop: 20 }} />}

      {result && (
        <View
          style={{
            marginTop: 20,
            backgroundColor: '#f3f4f6',
            padding: 15,
            borderRadius: 10,
          }}
        >
          <Text style={{ fontWeight: 'bold' }}>Reg Number: {result.reg_number}</Text>
          <Text>
            Score: {result.score} / {result.total}
          </Text>
        </View>
      )}
    </View>
  );
};

export default GradeScreen;
