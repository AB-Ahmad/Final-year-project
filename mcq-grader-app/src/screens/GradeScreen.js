export default function GradeScreen({ route, navigation }) {
  const { template, courseCode } = route.params;  // ✅ now passed from TemplatesScreen
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);

  const pickImage = async () => {
    let permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permissionResult.granted) {
      alert("Permission to access gallery is required!");
      return;
    }

    let pickerResult = await ImagePicker.launchImageLibraryAsync({
      allowsEditing: true,
      quality: 1,
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
    });

    if (!pickerResult.canceled) {
      const uri = pickerResult.assets[0].uri;
      setImage(uri);
    }
  };

  const uploadImage = async () => {
    if (!image) return;

    try {
      setLoading(true);

      const filename = image.split('/').pop();
      const base64 = await FileSystem.readAsStringAsync(image, {
        encoding: FileSystem.EncodingType.Base64,
      });

      const response = await fetch(`${BASE_URL}/grade_base64`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({
          filename,
          content: base64,
        }),
      });

      const data = await response.json();
      if (!data || !data.answers) {
        throw new Error("Invalid grading response");
      }

      // 🔹 Build details using template
      const details = [];
      let score = 0;
      template.forEach((correct, idx) => {
        const marked = data.answers[idx] || "";
        let status = "Blank";
        if (marked) {
          if (marked === correct) {
            status = "Correct ✅";
            score++;
          } else {
            status = `Wrong ❌ (marked ${marked})`;
          }
        }
        details.push({ question: idx + 1, marked, correct, status });
      });

      const result = {
        reg_number: data.reg_number || "UNKNOWN",
        score,
        total: template.length,
        courseCode,
        timestamp: new Date().toLocaleString(),
        details,
      };

      const existing = await AsyncStorage.getItem('gradedResults');
      const results = existing ? JSON.parse(existing) : [];
      results.push(result);
      await AsyncStorage.setItem('gradedResults', JSON.stringify(results));

      navigation.navigate('GradingResult', { result });

    } catch (error) {
      console.error("Upload failed:", error);
      Alert.alert("Upload failed", error.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.courseCode}>Course: {courseCode}</Text>

      <Button title="Pick an Image" onPress={pickImage} />

      {image && (
        <Image source={{ uri: image }} style={styles.image} />
      )}
      {image && (
        <Button title="Upload & Grade" onPress={uploadImage} />
      )}

      {loading && <ActivityIndicator size="large" color="#0000ff" />}
    </View>
  );
}
