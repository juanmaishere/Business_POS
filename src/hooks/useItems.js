import { useEffect, useState } from 'react'

export default function useItems(){
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const base = 'http://localhost:8000'

  useEffect(() => {
    let mounted = true
    fetch(`${base}/api/items`)
      .then(r => r.json())
      .then(data => { if(mounted){ setItems(data); setLoading(false) }})
      .catch(err => { console.error('fetch items', err); setLoading(false) })
    return ()=> mounted = false
  },[])
  console.log(items)
  return { items, loading }
}
