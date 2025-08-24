import React from 'react';
import { View, Text, StyleSheet, FlatList, Image } from 'react-native';

export default function GradingResultScreen({ route }) {
  const { result } = route.params;

  return (
    <FlatList
      data={result.details}
      keyExtractor={(item) => item.question.toString()}
      ListHeaderComponent={() => (
        <View>
          <Text style={styles.title}>Grading Result</Text>

          <Text style={styles.info}>Reg No: {result.reg_number}</Text>
          <Text style={styles.info}>Course: {result.courseCode}</Text>
          <Text style={styles.info}>Score: {result.score}/{result.total}</Text>
          <Text style={styles.info}>Date: {result.timestamp}</Text>

          {result.debug_image ? (
            <Image
              source={{ uri: `data:image/png;base64,${result.debug_image}` }}
              style={styles.debugImage}
              resizeMode="contain"
            />
          ) : (
            <Text style={styles.noImageText}>No debug image available</Text>
          )}

          <Text style={styles.subTitle}>Detailed Breakdown:</Text>
        </View>
      )}
      renderItem={({ item }) => (
        <View style={styles.row}>
          <Text style={styles.qText}>Q{item.question}:</Text>
          <Text
            style={[
              styles.answerText,
              item.status.includes("Correct") && { color: "green" },
              item.status.includes("Wrong") && { color: "red" },
              item.status.includes("Blank") && { color: "gray" },
            ]}
          >
            Marked: {item.marked || "-"} | Correct: {item.correct || "-"} | {item.status}
          </Text>
        </View>
      )}
      contentContainerStyle={styles.container}
    />
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, backgroundColor: 'white' },
  title: { fontSize: 22, fontWeight: 'bold', marginBottom: 20, textAlign: 'center' },
  info: { fontSize: 18, marginVertical: 6 },
  subTitle: { fontSize: 20, fontWeight: 'bold', marginVertical: 15 },
  row: { flexDirection: 'row', marginVertical: 4 },
  qText: { fontWeight: 'bold', marginRight: 10 },
  answerText: { flex: 1 },
  debugImage: { width: '100%', height: 400, marginVertical: 15, borderRadius: 8, borderWidth: 1, borderColor: '#ddd' },
  noImageText: { color: "gray", marginVertical: 10 },
});
